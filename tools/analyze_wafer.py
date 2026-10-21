"""Run the same live wafer diagnosis as both web pages without an LLM key."""
import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from src.data_analysis.dashboard import DashboardService
from src.data_analysis.inference import ModelService
from src.data_analysis.repository import SQLiteRepository
from src.data_analysis.service import DatasetService


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',type=Path,default=ROOT/'simulation/secom_test_batch_200811_200903.csv')
    parser.add_argument('--sample-id',required=True)
    parser.add_argument('--period',default='all')
    parser.add_argument('--review-ratio',type=float,default=.2)
    parser.add_argument('--include-drift',action='store_true')
    parser.add_argument('--include-global-shap',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with TemporaryDirectory(prefix='semiguard-diagnosis-') as tmp:
        service=DatasetService(SQLiteRepository(Path(tmp)/'analysis.sqlite3'),ModelService(ROOT))
        result=service.ingest('local-cli',args.file.name,args.file.read_bytes())
        tools=DashboardService(service).tools('local-cli',result['dataset_id'],args.period,args.review_ratio)
        report={'metadata':tools.metadata,'diagnosis':tools.diagnose_sample(args.sample_id,args.review_ratio)}
        if args.include_drift:report['sensor_drift']=tools.sensor_drift('all',20)
        if args.include_global_shap:report['global_shap']=tools.global_shap()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False), encoding="utf-8")
        d=report['diagnosis']
        print(json.dumps({'output':str(args.output.resolve()),'sample_id':args.sample_id,
            'scope_count':d['scope_count'],'risk_rank':d['row']['risk_rank'],
            'category':d['row']['category'],'rule':d['recommendation']['rule_id']},ensure_ascii=False))


if __name__=='__main__':main()
