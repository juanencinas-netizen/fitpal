from flask import Blueprint, render_template
from app.models import News

news_bp = Blueprint("news", __name__)


@news_bp.route("/")
def index():
    noticias = News.query.filter_by(published=True).order_by(News.created_at.desc()).all()
    return render_template("news/index.html", noticias=noticias)


@news_bp.route("/<int:news_id>")
def detail(news_id):
    noticia = News.query.filter_by(id=news_id, published=True).first_or_404()
    return render_template("news/detail.html", noticia=noticia)
