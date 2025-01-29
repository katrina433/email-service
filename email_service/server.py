import datetime as dt
import traceback

import uvicorn
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from email_service import database, models, orm


async def init_tables():
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

async def get_db():
    async with database.Session() as session:
        yield session

class Server:
    def __init__(self, reset_db: bool = False):
        self.app = FastAPI(on_startup=[init_tables] if reset_db else None)
        self.router = APIRouter()
        self.router.add_api_route("/nonprofit", self.get_nonprofit, methods=["GET"])
        self.router.add_api_route("/nonprofit", self.create_nonprofit, methods=["POST"])
        self.router.add_api_route("/nonprofit/{email_address}", self.delete_nonprofit, methods=["DELETE"])
        self.router.add_api_route("/email", self.get_email, methods=["GET"])
        self.router.add_api_route("/email", self.create_email, methods=["POST"])
        self.router.add_api_route("/templated_email", self.create_templated_email, methods=["POST"])
        self.app.include_router(self.router)
    
    async def get_nonprofit(
        self,
        email_address: str | None = None,
        name: str | None = None,
        address: str | None = None,
        db: AsyncSession = Depends(get_db),
    ):
        try:
            query = select(models.Nonprofit)
            if email_address is not None:
                query = query.filter(models.Nonprofit.email_address == email_address)
            if name is not None:
                query = query.filter(models.Nonprofit.name == name)
            if address is not None:
                query = query.filter(models.Nonprofit.address.conatins(address))
            res = await db.execute(query)
            return res.unique().scalars().all()
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Error {e}")
    
    async def create_nonprofit(self, nonprofit: orm.Nonprofit, db: AsyncSession = Depends(get_db)):
        try:
            db_nonprofit = models.Nonprofit(**nonprofit.model_dump())
            db.add(db_nonprofit)
            await db.commit()
        except IntegrityError as e:
            traceback.print_exc()
            raise HTTPException(status_code=422, detail=f"Invalid input {e}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal error {e}")

    async def delete_nonprofit(self, email_address: str, db: AsyncSession = Depends(get_db)):
        try:
            res = await db.execute(select(models.Nonprofit).filter(
                models.Nonprofit.email_address == email_address
            ))
            db_nonprofit = res.scalars().first()
            if not db_nonprofit:
                raise HTTPException(status_code=404, detail=f"Nonprofit not found for {email_address}")
            await db.delete(db_nonprofit)
            await db.commit()
        except HTTPException as e:
            raise e
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal error {e}")
    
    async def get_email(
        self,
        email_ids: str | None = None,
        recipient_addresses: str | None = None,
        start_time: dt.datetime | None = None,
        end_time: dt.datetime | None = None,
        db: AsyncSession = Depends(get_db)
    ):
        try:
            query = select(models.Email)
            if email_ids is not None:
                ids = [x.strip() for x in email_ids.split(",")]
                query = query.filter(models.Email.id.in_(ids))
            if recipient_addresses is not None:
                addr = [x.strip() for x in recipient_addresses.split(",")]
                query = query.filter(models.Email.recipients.any(models.EmailRecipient.email_address.in_(addr)))
            if start_time is not None:
                query = query.filter(models.Email.created_at >= start_time)
            if end_time is not None:
                query = query.filter(models.Email.created_at <= end_time)
            res = await db.execute(query)
            return res.unique().scalars().all()
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Error {e}")
    
    async def create_email(self, email: orm.Email, db: AsyncSession = Depends(get_db)):
        try:
            db_email = models.Email(**email.model_dump(exclude=["recipients", "cc", "bcc"]))
            db.add(db_email)
            await db.flush()
            db_recipients = [models.EmailRecipient(email_id=db_email.id, email_address=r) for r in email.recipients]
            db_cc = [models.EmailCc(email_id=db_email.id, email_address=r) for r in email.cc]
            db_bcc = [models.EmailBcc(email_id=db_email.id, email_address=r) for r in email.bcc]
            db.add_all(db_recipients)
            db.add_all(db_cc)
            db.add_all(db_bcc)
            await db.commit()
        except IntegrityError as e:
            traceback.print_exc()
            raise HTTPException(status_code=422, detail=f"Invalid input {e}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Error {e}")

    async def create_templated_email(self, template: orm.TemplatedEmail, db: AsyncSession = Depends(get_db)):
        try:
            nonprofit_res = await db.execute(select(models.Nonprofit).filter(
                models.Nonprofit.email_address.in_(template.recipients)
            ))
            db_nonprofits = nonprofit_res.unique().scalars().all()
            db_emails = [
                models.Email(
                    sender=template.sender,
                    subject=template.subject.format(**nonprofit.__dict__),
                    content=template.content.format(**nonprofit.__dict__),
                ) for nonprofit in db_nonprofits
            ]
            db.add_all(db_emails)
            await db.flush()
            db_recipients = [models.EmailRecipient(email_id=e.id, email_address=n.email_address) for e, n in zip(db_emails, db_nonprofits)]
            db_cc = []
            db_bcc = []
            for db_email in db_emails:
                for cc in template.cc:
                    db_cc.append(models.EmailCc(email_id=db_email.id, email_address = cc))
                for bcc in template.bcc:
                    db_bcc.append(models.EmailBcc(email_id=db_email.id, email_address = bcc))
            db.add_all(db_recipients)
            db.add_all(db_cc)
            db.add_all(db_bcc)
            await db.commit()
        except IntegrityError as e:
            traceback.print_exc()
            raise HTTPException(status_code=422, detail=f"Invalid input {e}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Error {e}")
        

if __name__ == "__main__":
    server = Server(reset_db=False)
    uvicorn.run(server.app, host="127.0.0.1", port=8000)
