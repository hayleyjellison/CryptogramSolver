from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..find_word import find_possible_matches

app = FastAPI(title="Cryptogram Solver", version="1.0.0")


@app.get("/")
def read_root():
    return {"Hello": "World"}


class WordRequest(BaseModel):
    sample_word: str = Field()
    known_letters: str = Field()


@app.post("/solve")
def solve_word(request: dict) -> set[str]:
    sample_word = request.get("sample_word")
    known_letters = request.get("known_letters")
    possible_matches = find_possible_matches(sample_word, known_letters)

    return possible_matches
