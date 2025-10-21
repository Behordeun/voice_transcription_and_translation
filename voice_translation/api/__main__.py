import uvicorn

from .main import app


def main():
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
