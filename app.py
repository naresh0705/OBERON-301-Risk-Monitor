import os, io, tempfile, shutil
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from risk_scoring import RiskScoringEngine

app = FastAPI(title="Risk-Based Data Quality Monitor v3")
templates = Jinja2Templates(directory="templates")
engine_store = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/analyze")
async def analyze(demographics: UploadFile = File(...), medical_history: UploadFile = File(...), concomitant_meds: UploadFile = File(...), adverse_events: UploadFile = File(...), lab_data: UploadFile = File(...), vital_signs: UploadFile = File(...), disposition: UploadFile = File(...), query_detail: UploadFile = File(...), protocol_deviations: UploadFile = File(...), visit_tracking: UploadFile = File(...)):
    try:
        td = tempfile.mkdtemp()
        fm = {"demographics": demographics, "medical_history": medical_history, "concomitant_meds": concomitant_meds, "adverse_events": adverse_events, "lab_data": lab_data, "vital_signs": vital_signs, "disposition": disposition, "query_detail": query_detail, "protocol_deviations": protocol_deviations, "visit_tracking": visit_tracking}
        fd = {}
        for key, uf in fm.items():
            fp = os.path.join(td, f"{key}.csv")
            content = await uf.read()
            with open(fp, "wb") as f:
                f.write(content)
            fd[key] = fp
        engine = RiskScoringEngine()
        engine.load_data(fd)
        engine.score_all_subjects()
        engine_store["current"] = engine
        summary = engine.get_summary()
        shutil.rmtree(td)
        return JSONResponse(content=summary)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/subject/{subject_id}")
async def subject_detail(subject_id: str):
    engine = engine_store.get("current")
    if not engine:
        return JSONResponse(content={"error": "No analysis run yet"}, status_code=400)
    detail = engine.get_subject_detail(subject_id)
    if not detail:
        return JSONResponse(content={"error": "Subject not found"}, status_code=404)
    return JSONResponse(content=detail)


@app.get("/export")
async def export_csv():
    engine = engine_store.get("current")
    if not engine:
        return JSONResponse(content={"error": "No analysis run yet"}, status_code=400)
    df = engine.export_to_csv()
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(io.BytesIO(stream.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=risk_scores_export.csv"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
