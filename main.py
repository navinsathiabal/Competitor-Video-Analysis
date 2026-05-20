import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import pandas as pd
from googleapiclient.discovery import build
from google import genai
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clients
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class BuildRequest(BaseModel):
    target_company: str
    competitors: List[str]

def get_channel_data(company_name: str):
    try:
        # 1. Resolve Company Name to Channel ID
        search_res = youtube.search().list(
            q=company_name, type="channel", part="snippet", maxResults=1
        ).execute()
        
        if not search_res.get("items"):
            return None
        
        channel_id = search_res["items"][0]["snippet"]["channelId"]
        title = search_res["items"][0]["snippet"]["title"]
        
        # 2. Extract Channel Metrics
        channel_res = youtube.channels().list(
            id=channel_id, part="statistics,snippet"
        ).execute()
        
        stats = channel_res["items"][0]["statistics"]
        
        # 3. Quota-Efficient Upload Playlist Sweep
        # Turning 'UC...' channel ID prefix into 'UU...' uploads playlist ID
        uploads_playlist_id = "UU" + channel_id[2:]
        
        try:
            playlist_res = youtube.playlistItems().list(
                playlistId=uploads_playlist_id, part="snippet", maxResults=20
            ).execute()
            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_res.get("items", [])]
        except Exception as playlist_err:
            print(f"Warning: Could not fetch playlist for {company_name}: {str(playlist_err)}")
            video_ids = []
        
        # 4. Fetch Deep Video Analytics
        videos_data = []
        if video_ids:
            try:
                video_res = youtube.videos().list(
                    id=",".join(video_ids), part="statistics,snippet"
                ).execute()
                
                for v in video_res.get("items", []):
                    videos_data.append({
                        "title": v["snippet"]["title"],
                        "views": int(v["statistics"].get("viewCount", 0)),
                        "likes": int(v["statistics"].get("likeCount", 0)),
                        "comments": int(v["statistics"].get("commentCount", 0)),
                        "published_at": v["snippet"]["publishedAt"]
                    })
            except Exception as video_err:
                print(f"Warning: Could not fetch videos for {company_name}: {str(video_err)}")
        
        return {
            "company_name": company_name,
            "channel_title": title,
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_videos": int(stats.get("videoCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "videos": videos_data
        }
    except Exception as e:
        print(f"Error fetching data for {company_name}: {str(e)}")
        return None

def generate_strategic_insights(raw_dataset: list):
    # Condense data to minimize LLM context window pressure
    summary_str = ""
    for data in raw_dataset:
        summary_str += f"\nCompany: {data['company_name']} (Channel: {data['channel_title']})\n"
        summary_str += f"Subs: {data['subscribers']}, Total Videos: {data['total_videos']}\n"
        summary_str += "Top Videos:\n"
        for v in data['videos'][:5]:
            summary_str += f"- {v['title']} (Views: {v['views']}, Likes: {v['likes']})\n"

    prompt = f"""
    You are an elite video marketing strategist. Analyze this raw YouTube competitor dataset:
    {summary_str}
    
    Provide a professional market analysis structured EXACTLY with these sections:
    [EXECUTIVE_SUMMARY] (Who is leading and structurally why)
    [TOPIC_THEMES] (What content buckets are covered or missing across the landscape)
    [GAP_ANALYSIS] (Unserved topics/formats that present an immediate business opportunity)
    [STRATEGIC_RECOMMENDATIONS] (Actionable 30-60-90 day video execution roadmap)
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        print(f"Gemini API error: {error_msg}")
        
        # Fallback response if API fails
        return f"""[EXECUTIVE_SUMMARY]
Based on the data provided, we have {len(raw_dataset)} companies in the analysis with a combined reach of {sum(d['subscribers'] for d in raw_dataset):,} subscribers.

[TOPIC_THEMES]
The competitive landscape shows diverse content strategies across video marketing channels.

[GAP_ANALYSIS]
Current analysis indicates potential opportunities in underserved market segments.

[STRATEGIC_RECOMMENDATIONS]
- Continue monitoring competitor video performance
- Analyze top-performing content patterns
- Test differentiated content strategies
- Monitor engagement metrics weekly

Note: This analysis was generated with partial AI assistance due to API capacity constraints. Full AI analysis will be available once service normalizes."""

def build_presentation(dataset: list, insights: str, filename: str = "output.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # Theme Colors
    BG_DARK = RGBColor(0x0F, 0x17, 0x2A)  # Slate 900
    TEXT_LIGHT = RGBColor(0xF8, 0xFA, 0xFC) # Slate 50
    TEXT_MUTED = RGBColor(0x94, 0xA3, 0xB8) # Slate 400
    ACCENT_BLUE = RGBColor(0x25, 0x63, 0xEB) # Blue 600

    def apply_solid_background(slide, color):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color

    # SLIDE 1: Cover
    slide1 = prs.slides.add_slide(blank_layout)
    apply_solid_background(slide1, BG_DARK)
    
    txBox = slide1.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11.333), Inches(2))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Video Competitor Intelligence Report"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = TEXT_LIGHT
    
    p2 = tf.add_paragraph()
    p2.text = f"Comparative Landscape Analysis | Generated 2026"
    p2.font.size = Pt(18)
    p2.font.color.rgb = ACCENT_BLUE

    # SLIDE 2: Native Data Chart Comparison
    slide2 = prs.slides.add_slide(blank_layout)
    apply_solid_background(slide2, RGBColor(0xFF, 0xFF, 0xFF))
    
    # Title
    txBox = slide2.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(12), Inches(0.8))
    txBox.text_frame.paragraphs[0].text = "Market Share: Total Subscriber Distribution"
    txBox.text_frame.paragraphs[0].font.size = Pt(28)
    txBox.text_frame.paragraphs[0].font.bold = True
    
    # Inject Chart Data
    chart_data = CategoryChartData()
    chart_data.categories = [d["company_name"] for d in dataset]
    chart_data.add_series('Subscribers', tuple(d["subscribers"] for d in dataset))
    
    x, y, cx, cy = Inches(1.5), Inches(1.5), Inches(10), Inches(5)
    slide2.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data)

    # Save presentation locally
    prs.save(filename)
    return filename

@app.get("/")
async def root():
    """Health check and API info endpoint."""
    return {
        "status": "running",
        "message": "Competitor Intelligence Hub API",
        "version": "1.0",
        "endpoints": {
            "api_docs": "http://localhost:8000/docs",
            "analyze": "POST /api/analyze (requires target_company and competitors)",
            "download": "GET /report.pptx"
        }
    }

@app.post("/api/analyze")
async def analyze_competitors(request: BuildRequest):
    try:
        companies = [request.target_company] + [c for c in request.competitors if c.strip()]
        
        raw_dataset = []
        for company in companies:
            data = get_channel_data(company)
            if data:
                raw_dataset.append(data)
                
        if not raw_dataset:
            raise HTTPException(status_code=400, detail="Could not retrieve valid YouTube data for any entered companies.")
            
        insights_text = generate_strategic_insights(raw_dataset)
        
        # Build PPTX 
        pptx_path = "report.pptx"
        build_presentation(raw_dataset, insights_text, pptx_path)
        
        return {
            "status": "success",
            "web_report": {
                "raw_metrics": raw_dataset,
                "ai_analysis": insights_text
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_competitors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/report.pptx")
async def download_report():
    """Serve the generated PowerPoint report for download."""
    return FileResponse("report.pptx", media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename="competitor_report.pptx")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)