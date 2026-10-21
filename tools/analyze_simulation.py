"""Run the shared inference/EDA pipeline locally without an LLM API key."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_analysis.inference import ModelService
from src.data_analysis.repository import SQLiteRepository
from src.data_analysis.service import DatasetService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, help='One CSV; defaults to all simulation/*.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/analysis_reports')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    model = ModelService(ROOT)
    if model.error:
        raise SystemExit(model.error)
    service = DatasetService(SQLiteRepository(args.output / 'analysis.sqlite3'), model)
    summary = []
    for path in [args.file] if args.file else sorted((ROOT / 'simulation').glob('*.csv')):
        result = service.ingest('local-analysis-cli', path.name, path.read_bytes(), 'simulation' if path.parent.resolve() == (ROOT / 'simulation').resolve() else 'upload')
        report = result['report']
        report['highest_risk_samples'] = service.tools('local-analysis-cli', result['dataset_id']).execute('rank_samples', {'limit': 10})
        tools = {r['tool']: r['data'] for r in report['results']}
        profile, metrics = tools['profile_dataset'], tools['evaluate_predictions']
        summary.append({'filename':path.name, 'rows':profile['row_count'], 'missing_cells':profile['missing_cells'], 'known_labels':profile['known_label_count'], 'confirmed_failures':profile['confirmed_failures'], 'top20_recall':metrics.get('recall'), 'model_version':model.version})
        target = args.output / f'{path.stem}.json'
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        print(f'{path.name}: {profile["row_count"]} rows, {profile["missing_cells"]} missing sensor cells -> {target}')
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# simulation 추론·기본 분석 결과', '', '실제 저장 모델과 공통 데이터 파이프라인으로 계산했다. 합성 검증 CSV이며 실제 설비의 성능·원인 근거로 일반화하지 않는다.', '', '|파일|행|결측 센서 셀|확인 불량|상위 20% Recall|', '|---|---:|---:|---:|---:|']
    for r in summary:
        recall = f'{r["top20_recall"]:.2%}' if r['top20_recall'] is not None else '미확인'
        lines.append(f'|{r["filename"]}|{r["rows"]}|{r["missing_cells"]}|{r["confirmed_failures"]}|{recall}|')
    lines.extend(['', f'모델 버전: `{model.version}`', '', '각 JSON에는 결측·분포, 위험군 센서 차이, 센서 상관, 실제 월별 표본 수·위험도, SECOM 학습 정상군 비교와 라벨 기반 평가가 포함된다.'])
    (args.output / 'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
