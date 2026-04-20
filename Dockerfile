FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv && uv sync

CMD ["uv", "run", "streamlit", "run", "gui.py"]