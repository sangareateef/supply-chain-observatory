from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Interface"])
templates = Jinja2Templates(directory="app/templates")


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
    )