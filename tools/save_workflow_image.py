import os
import shutil

src = r"C:\Users\박주형\.gemini\antigravity-ide\brain\13881c84-7554-4918-9233-b93b89ace6b6\service_data_workflow_1792456202339.jpg"

picture_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "picture")

# Remove any corrupted names from earlier attempt
for f in os.listdir(picture_dir):
    if "" in f and "SEMI_GUARD" in f:
        try:
            os.remove(os.path.join(picture_dir, f))
            print("Removed corrupted file:", f)
        except Exception:
            pass

dst_png = os.path.join(picture_dir, "SEMI_GUARD_data_workflow_architecture.png")
dst_jpg = os.path.join(picture_dir, "SEMI_GUARD_data_workflow_architecture.jpg")
dst_kr_png = os.path.join(picture_dir, "SEMI_GUARD_데이터_워크플로우_아키텍처.png")

shutil.copyfile(src, dst_png)
shutil.copyfile(src, dst_jpg)
shutil.copyfile(src, dst_kr_png)

print("Saved files successfully:")
print("1.", dst_png)
print("2.", dst_jpg)
print("3.", dst_kr_png)
