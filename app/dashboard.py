from fastapi import APIRouter, Depends, File, UploadFile, HTTPException,Form,status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
import json
from datetime import datetime
from sqlalchemy.orm import Session
from .database import get_db
from datetime import datetime
from . import models
from . import schemas


router = APIRouter()

@router.get("/dashboard")
def dashboard(db : Session = Depends(get_db)):
    try:
        customers = db.query(models.Customers).count()
        due_date = db.query(models.Customers).filter(models.Customers.end_date < datetime.now().date().isoformat()).count() 
        pending = db.query(models.Customers).filter(models.Customers.status == "pending").count()
        completed = db.query(models.Customers).filter(models.Customers.status == "completed").count()

        if not customers:
            raise HTTPException(status_code=404, detail="No customers found")

        return json.dumps({
            "total": customers,
            "due_date":due_date,
            "pending": pending,
            "completed" : completed
        })

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)
    

@router.get("/due_customers", response_model=list[schemas.CustomerOut])  # Use list as the response model for multiple customers
def due_customers(db: Session = Depends(get_db)):
    try:
        customers = db.query(models.Customers).filter(models.Customers.end_date < datetime.now().date()).all()  # Use .all() to get all matching customers

        if not customers:
            raise HTTPException(status_code=404, detail="No due customers found")

        return [schemas.CustomerOut.from_orm(customer) for customer in customers]

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)


@router.get("/pending_customers", response_model=list[schemas.CustomerOut])  # Use list as the response model for multiple customers
def pending_customers(db: Session = Depends(get_db)):
    try:
        customers = db.query(models.Customers).filter(models.Customers.status == "pending").all()  # Use .all() to get all matching customers

        if not customers:
            raise HTTPException(status_code=404, detail="No Pending customers found")

        return [schemas.CustomerOut.from_orm(customer) for customer in customers]

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)
    
@router.get("/completed_customers", response_model=list[schemas.CustomerOut])  # Use list as the response model for multiple customers
def completed_customers(db: Session = Depends(get_db)):
    try:
        customers = db.query(models.Customers).filter(models.Customers.status == "completed").all()  # Use .all() to get all matching customers

        if not customers:
            raise HTTPException(status_code=404, detail="No Pending customers found")

        return [schemas.CustomerOut.from_orm(customer) for customer in customers]

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)
        

        