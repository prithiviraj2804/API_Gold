from fastapi import APIRouter, Depends, File, UploadFile, HTTPException,Form
import os,json
from sqlalchemy.orm import Session
from .database import get_db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi.responses import JSONResponse
from typing import List
from . import models
from . import schemas

router = APIRouter()

IMAGE_DIR = "images"

@router.post("/add_customers")
def add_customers(
    app_no: int = Form(...),
    username: str = Form(...),
    address: str = Form(...),
    ph_no: str = Form(...),
    item_weight: int = Form(...),
    amount: int = Form(...),
    pending: int = Form(...),
    current_amount: int = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    note: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        image_filename = f"{username}_{app_no}.jpg"
        image_path = os.path.join(IMAGE_DIR, image_filename)

        new_customer = models.Customers(
            app_no=app_no,
            username=username,
            address=address,
            ph_no=ph_no,
            item_weight=item_weight,
            amount=amount,
            pending=pending,
            current_amount=current_amount, 
            start_date=start_date,
            end_date=end_date,
            note=note,
            image=image_path  
        )
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

        with open(image_path, "wb") as image_file:
            image_file.write(image.file.read())
        
        return {"message": "New customer entry added successfully"}

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/customers", response_model=list[schemas.CustomerOut])
def get_customers(db: Session = Depends(get_db)):
    try:
        customers = db.query(models.Customers).all()

        if not customers:
            raise HTTPException(status_code=404, detail="No customers found")

        return [schemas.CustomerOut.model_validate(customer) for customer in customers]
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)


@router.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    try:
        customer = db.query(models.Customers).filter(models.Customers.app_no == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return schemas.CustomerOut.from_orm(customer)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)


@router.get("/filter/{number}", response_model=list[schemas.CustomerOut])
def get_customers_by_ph_no(number: str, db: Session = Depends(get_db)):
    try:
        details = db.query(models.Customers).filter(models.Customers.ph_no == number).all() 

        if not details:
            raise HTTPException(status_code=404, detail=f"No customers found with phone number: {number}")

        return [schemas.CustomerOut.from_orm(customer) for customer in details]

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except Exception as e:
        return JSONResponse(content={"msg":e},status_code=500)


@router.put("/customers/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(
    customer_id: int,
    app_no: int = Form(...),
    username: str = Form(...),
    address: str = Form(...),
    ph_no: str = Form(...),
    item_weight: int = Form(...),
    amount: int = Form(...),
    current_amount: int = Form(...),  # Optional field
    start_date: str = Form(...),
    end_date: str = Form(...),
    note: str = Form(...),
    status: str = Form(...),
    image: UploadFile = File(None),  # Optional image
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(models.Customers).filter(models.Customers.app_no == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Ensure valid status is provided
        if status not in [models.StatusEnum.pending.value, models.StatusEnum.completed.value]:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        customer.status = status

        # Handle payment history if current_amount is provided
        if current_amount:
            payment_history = json.loads(customer.payment_history) if customer.payment_history else []

            current_amount_data = {
                "payment": current_amount,
                "date": datetime.now().date().isoformat()
            }

            payment_history.append(current_amount_data)

            total_payments = sum([entry["payment"] for entry in payment_history])

            # Update pending amount
            new_pending = amount - total_payments
            customer.pending = new_pending

            # Save updated payment history
            customer.payment_history = json.dumps(payment_history)

        # Update customer fields
        customer.app_no = app_no
        customer.username = username
        customer.address = address
        customer.ph_no = ph_no
        customer.item_weight = item_weight
        customer.amount = amount
        customer.current_amount = current_amount
        customer.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        customer.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        customer.note = note

        # Handle image update
        if image:
            if customer.image and os.path.exists(customer.image):
                os.remove(customer.image)

            image_filename = f"{username}_{app_no}.jpg"
            image_path = os.path.join(IMAGE_DIR, image_filename)

            with open(image_path, "wb") as image_file:
                image_file.write(image.file.read())

            customer.image = image_path

        # Commit changes to the database
        db.commit()
        db.refresh(customer)

        return customer

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Application Number must be unique. Integrity error occurred.")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(e)}")
    
    except Exception as e:
        # Log the error to see exactly what happened
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
