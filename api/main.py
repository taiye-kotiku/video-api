from workers.render import render_textoverlay
from arq import create_pool

@app.post("/generate/textoverlay")
async def generate_textoverlay(payload: dict):
    redis = await create_pool(settings.redis_url)
    job = await redis.enqueue_job("render_textoverlay",
                                  payload["video_url"],
                                  payload["title"],
                                  payload.get("quality", "final"))
    return {"jobId": job.job_id, "statusUrl": f"/status/{job.job_id}"}

@app.get("/status/{job_id}")
async def job_status(job_id: str):
    redis = await create_pool(settings.redis_url)
    job = await redis._get_job_by_id(job_id)
    if not job:
        return {"error": "not found"}
    return {"status": job.status, "result": job.result}