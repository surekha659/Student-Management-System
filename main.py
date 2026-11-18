from fastapi import FastAPI, Request, Form, status
import fastapi
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse
import sqlite3


def get_connection():
    connection = sqlite3.connect("student.db")
    return connection


def create_table():
    connection = get_connection()
    cursor = connection.cursor()

    q = """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        Age INTEGER,
        gender TEXT,
        marks INTEGER,
        course TEXT,
        image TEXT,
        status INTEGER
    )
    """

    cursor.execute(q)
    connection.commit()
    connection.close()


create_table()


class student(BaseModel):
    name: str
    age: int = Field(ge=18, le=30)
    gender: str
    marks: int = Field(ge=0, le=100)
    course: str
    image: str = ""
    status: int = Field(ge=0, le=1)


templates = Jinja2Templates(directory="templates")
app = FastAPI()


@app.get("/")
def home_page(request: Request):
    search = request.query_params.get("search", "").strip()
    filter_by = request.query_params.get("filter_by", "all")

    if filter_by not in ["all", "name", "course"]:
        filter_by = "all"

    connection = get_connection()
    cursor = connection.cursor()

    q = "SELECT * FROM students"
    values = ()

    if search:
        pattern = f"%{search}%"

        if filter_by == "name":
            q += " WHERE name LIKE ? COLLATE NOCASE"
            values = (pattern,)

        elif filter_by == "course":
            q += " WHERE course LIKE ? COLLATE NOCASE"
            values = (pattern,)

        else:
            q += """
            WHERE name LIKE ? COLLATE NOCASE
            OR course LIKE ? COLLATE NOCASE
            """
            values = (pattern, pattern)

    q += " ORDER BY id DESC"

    cursor.execute(q, values)
    students = cursor.fetchall()
    connection.close()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "stds": students,
            "search": search,
            "filter_by": filter_by,
        },
    )


@app.get("/students/add")
def send_std_form(req: Request):
    return templates.TemplateResponse(
        request=req,
        name="add-student.html",
        context={},
    )


@app.post("/students/add")
def create_std(
    name=Form(),
    age=Form(),
    gender=Form(),
    marks=Form(),
    course=Form(),
    image=Form(""),
    status=Form(0),
):
    std_obj = student(
        name=name,
        age=age,
        gender=gender,
        marks=marks,
        course=course,
        image=image,
        status=status,
    )

    values = (
        std_obj.name,
        std_obj.age,
        std_obj.gender,
        std_obj.marks,
        std_obj.course,
        std_obj.image,
        std_obj.status,
    )

    connection = get_connection()
    cursor = connection.cursor()

    q = """
    INSERT INTO students
    (name, Age, gender, marks, course, image, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(q, values)
    connection.commit()
    connection.close()

    return RedirectResponse(
        url="/",
        status_code=fastapi.status.HTTP_303_SEE_OTHER,
    )

@app.get("/students/edit/{std_id}")
def edit_std(req: Request, std_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
        (std_id,),
    )
    std = cursor.fetchone()
    connection.close()

    if std is None:
        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=req,
        name="edit.html",
        context={"std": std},
    )


@app.post("/students/edit/{std_id}")
def update_std(
    std_id: int,
    name: str = Form(...),
    age: int = Form(..., ge=18, le=30),
    gender: str = Form(...),
    marks: int = Form(..., ge=0, le=100),
    course: str = Form(...),
    image: str = Form(""),
    status: int = Form(0, ge=0, le=1),
):
    std_obj = student(
        name=name,
        age=age,
        gender=gender,
        marks=marks,
        course=course,
        image=image,
        status=status,
    )

    values = (
        std_obj.name,
        std_obj.age,
        std_obj.gender,
        std_obj.marks,
        std_obj.course,
        std_obj.image,
        std_obj.status,
        std_id,
    )

    connection = get_connection()
    cursor = connection.cursor()

    q = """
    UPDATE students
    SET name = ?, Age = ?, gender = ?, marks = ?,
        course = ?, image = ?, status = ?
    WHERE id = ?
    """

    cursor.execute(q, values)
    connection.commit()
    connection.close()

    return RedirectResponse(
        url=f"/students/{std_id}",
        status_code=fastapi.status.HTTP_303_SEE_OTHER,
    )


@app.get("/students/{std_id}")
def single_std(req: Request, std_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
        (std_id,),
    )
    std = cursor.fetchone()
    connection.close()

    if std is None:
        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=req,
        name="single-std.html",
        context={"std": std},
    )


@app.post("/students/{std_id}/delete")
def delete_std(std_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (std_id,),
    )

    connection.commit()
    connection.close()

    return RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER,
    )


