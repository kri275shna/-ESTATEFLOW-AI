import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.entities import (
    User, UserRole, Project, PropertyFact,
    Lead, LeadStatus, LeadSource,
    VisitSlot, Booking, BookingStatus,
    Conversation, Message, Handoff, MarketingSpend
)


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "admin@estateflow.ai").first():
            print("Database already seeded. Skipping initial user creation.")
            return

        print("Seeding database with Company A (Ahmedabad) sample data...")

        # 1. Create Users
        users = [
            User(
                email="admin@estateflow.ai",
                hashed_password=get_password_hash("Admin@123"),
                full_name="Rajesh Parekh (Director)",
                role=UserRole.ADMIN,
                phone="+919825000001",
                is_active=True
            ),
            User(
                email="saleshead@estateflow.ai",
                hashed_password=get_password_hash("Head@123"),
                full_name="Bhavin Shah (Sales Head)",
                role=UserRole.SALES_HEAD,
                phone="+919825000002",
                is_active=True
            ),
            User(
                email="buyer@estateflow.ai",
                hashed_password=get_password_hash("Buyer@123"),
                full_name="Gaurav Mehta (Prospective Buyer)",
                role=UserRole.BUYER,
                phone="+919825000099",
                is_active=True
            ),
        ]

        # 11 Sales Executives
        sales_exec_names = [
            ("rahul.sales@estateflow.ai", "Rahul Sharma", "+919825010001"),
            ("priya.sales@estateflow.ai", "Priya Mehta", "+919825010002"),
            ("amit.sales@estateflow.ai", "Amit Patel", "+919825010003"),
            ("sneha.sales@estateflow.ai", "Sneha Desai", "+919825010004"),
            ("vikram.sales@estateflow.ai", "Vikram Shah", "+919825010005"),
            ("anjali.sales@estateflow.ai", "Anjali Varma", "+919825010006"),
            ("jayesh.sales@estateflow.ai", "Jayesh Trivedi", "+919825010007"),
            ("pooja.sales@estateflow.ai", "Pooja Solanki", "+919825010008"),
            ("hiren.sales@estateflow.ai", "Hiren Rawal", "+919825010009"),
            ("meera.sales@estateflow.ai", "Meera Joshi", "+919825010010"),
            ("chirag.sales@estateflow.ai", "Chirag Panchal", "+919825010011"),
        ]

        for email, name, phone in sales_exec_names:
            users.append(
                User(
                    email=email,
                    hashed_password=get_password_hash("Sales@123"),
                    full_name=name,
                    role=UserRole.SALES_EXECUTIVE,
                    phone=phone,
                    is_active=True
                )
            )

        db.add_all(users)
        db.commit()

        # Reload sales reps
        sales_reps = db.query(User).filter(User.role == UserRole.SALES_EXECUTIVE).all()
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()

        # 2. Create 2 Live Residential Projects
        project1 = Project(
            code="PROJECT-1",
            name="Harmony Enclave",
            location="Shela, Off Club O7 Road, Ahmedabad",
            rera_number="PR/GJ/AHMEDABAD/AUDA/RAA09876/011124",
            total_units=210,
            min_price=6500000,   # ₹65 Lakh
            max_price=9500000,   # ₹95 Lakh
            configurations="2 BHK, 3 BHK",
            possession_date="March 2027",
            brochure_url="https://estateflow.ai/brochures/harmony-enclave.pdf",
            latitude=22.9984,
            longitude=72.4645,
            is_active=True
        )

        project2 = Project(
            code="PROJECT-2",
            name="Skyline Serenity",
            location="SG Highway, Near Vaishno Devi Circle, Ahmedabad",
            rera_number="PR/GJ/AHMEDABAD/AHMEDABAD CITY/RAA08765/150824",
            total_units=210,
            min_price=8500000,   # ₹85 Lakh
            max_price=12000000,  # ₹1.20 Crore
            configurations="2 BHK, 3 BHK Luxury",
            possession_date="December 2026",
            brochure_url="https://estateflow.ai/brochures/skyline-serenity.pdf",
            latitude=23.1185,
            longitude=72.5412,
            is_active=True
        )

        db.add_all([project1, project2])
        db.commit()

        # 3. Create Approved Property Fact Sheets
        facts = [
            # Harmony Enclave Facts
            PropertyFact(
                project_id=project1.id,
                category="Configuration & Carpet Area",
                attribute_name="2 BHK Carpet Area",
                approved_fact="2 BHK units offer 725 sq.ft. to 780 sq.ft. RERA carpet area with 2 master bedrooms, 2 bathrooms, and a private utility balcony.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project1.id,
                category="Configuration & Carpet Area",
                attribute_name="3 BHK Carpet Area",
                approved_fact="3 BHK units offer 1,020 sq.ft. to 1,110 sq.ft. RERA carpet area with 3 bedrooms, 3 bathrooms, spacious foyer, and cross-ventilation layout.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project1.id,
                category="Pricing & Payment Terms",
                attribute_name="Price Range",
                approved_fact="2 BHK ranges from ₹65 Lakh to ₹78 Lakh. 3 BHK ranges from ₹82 Lakh to ₹95 Lakh. Final price depends on floor rise, unit orientation, and statutory charges.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project1.id,
                category="Amenities",
                attribute_name="Recreation & Clubhouse",
                approved_fact="Features a 20,000 sq.ft. clubhouse, temperature-regulated swimming pool, squash court, indoor badminton, multipurpose community hall, and senior citizen sit-out.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project1.id,
                category="Possession & Approvals",
                attribute_name="RERA & Possession",
                approved_fact="Approved under Gujarat RERA Reg No. PR/GJ/AHMEDABAD/AUDA/RAA09876/011124. Possession date is March 2027.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project1.id,
                category="Location & Connectivity",
                attribute_name="Surroundings & Proximity",
                approved_fact="Located in Shela, 4 minutes from Club O7, 8 minutes from SP Ring Road, and 12 minutes from South Bopal commercial hub.",
                is_public=True,
                updated_by=admin_user.id
            ),

            # Skyline Serenity Facts
            PropertyFact(
                project_id=project2.id,
                category="Configuration & Carpet Area",
                attribute_name="2 BHK Carpet Area",
                approved_fact="2 BHK luxury apartments provide 830 sq.ft. RERA carpet area with 10.5 ft floor-to-ceiling clear height and imported Italian vitrified tiling.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project2.id,
                category="Configuration & Carpet Area",
                attribute_name="3 BHK Carpet Area",
                approved_fact="3 BHK luxury apartments span 1,220 sq.ft. to 1,350 sq.ft. carpet area with servant quarters, expansive 28 ft living deck, and modular Italian kitchen provisions.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project2.id,
                category="Pricing & Payment Terms",
                attribute_name="Price Range",
                approved_fact="2 BHK starts from ₹85 Lakh up to ₹96 Lakh. 3 BHK ranges from ₹1.02 Crore to ₹1.20 Crore. Stamp duty and GST are payable as per Gujarat state norms.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project2.id,
                category="Amenities",
                attribute_name="Luxury Amenities",
                approved_fact="Offers a 22nd-floor Sky Lounge, rooftop infinity pool overlooking SG Highway, 3-tier biometric access, private EV charging for each parking slot, and co-working conference suites.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project2.id,
                category="Possession & Approvals",
                attribute_name="RERA & Possession",
                approved_fact="Approved under Gujarat RERA Reg No. PR/GJ/AHMEDABAD/AHMEDABAD CITY/RAA08765/150824. Possession commitment is December 2026.",
                is_public=True,
                updated_by=admin_user.id
            ),
            PropertyFact(
                project_id=project2.id,
                category="Location & Connectivity",
                attribute_name="SG Highway Connectivity",
                approved_fact="Situated right on SG Highway, 3 minutes from Vaishno Devi Circle, 10 minutes from Nirma University, and 20 minutes from Sardar Vallabhbhai Patel International Airport.",
                is_public=True,
                updated_by=admin_user.id
            ),
        ]

        db.add_all(facts)
        db.commit()

        # 4. Create Visit Slots (Past, Today, and Next 14 Days)
        now = datetime.now(timezone.utc)
        base_date = now.replace(hour=10, minute=0, second=0, microsecond=0)

        slots_to_add = []
        for day_offset in range(-7, 15):
            slot_day = base_date + timedelta(days=day_offset)
            # Create 3 slots per day for each project: 11:00 AM, 2:30 PM, 5:00 PM
            for proj in [project1, project2]:
                for hour, minute in [(11, 0), (14, 30), (17, 0)]:
                    s_start = slot_day.replace(hour=hour, minute=minute)
                    s_end = s_start + timedelta(hours=1)
                    slots_to_add.append(
                        VisitSlot(
                            project_id=proj.id,
                            slot_start=s_start,
                            slot_end=s_end,
                            max_capacity=3,
                            booked_count=0,
                            is_blocked=False
                        )
                    )

        db.add_all(slots_to_add)
        db.commit()

        # Reload some slots
        all_slots = db.query(VisitSlot).order_by(VisitSlot.slot_start).all()
        slot_map = {(s.project_id, s.slot_start.strftime("%Y-%m-%d %H:%M")): s for s in all_slots}

        # 5. Create Realistic Leads (at least 30) including explicit sample leads
        leads_data = [
            # Explicit Sample Record 1
            {
                "reference": "LD-58210",
                "name": "Hardik Patel",
                "phone": "+919825158210",
                "raw_phone": "98251 58210",
                "email": "hardik.patel@gmail.com",
                "source": LeadSource.PROPERTY_PORTAL,
                "project": project1,
                "bhk": "3 BHK",
                "budget_min": 8500000,
                "budget_max": 9500000,
                "timeline": "Immediate (0-1 mo)",
                "status": LeadStatus.VISIT_BOOKED,
                "score": 90,
                "is_qualified": True,
                "sales_exec": sales_reps[0],
                "book_slot_offset": 2,  # 2 days in future 11:00 AM
                "book_status": BookingStatus.CONFIRMED,
            },
            # Explicit Sample Record 2
            {
                "reference": "LD-58211",
                "name": "Nidhi Shah",
                "phone": "+919825158211",
                "raw_phone": "09825158211",
                "email": "nidhi.shah@yahoo.co.in",
                "source": LeadSource.SOCIAL_MEDIA,
                "project": project2,
                "bhk": "2 BHK",
                "budget_min": 8000000,
                "budget_max": 9000000,
                "timeline": "1-3 months",
                "status": LeadStatus.CONTACTED,
                "score": 75,
                "is_qualified": True,
                "sales_exec": sales_reps[1],
                "book_slot_offset": None,
                "book_status": None,
            },
            # Explicit Sample Record 3
            {
                "reference": "LD-58224",
                "name": "Kavita Joshi",
                "phone": "+919825158224",
                "raw_phone": "+91-98251-58224",
                "email": "kavita.joshi@rediffmail.com",
                "source": LeadSource.HOARDING,
                "project": project2,
                "bhk": "2 BHK",
                "budget_min": 8500000,
                "budget_max": 9500000,
                "timeline": "1-3 months",
                "status": LeadStatus.VISITED,
                "score": 85,
                "is_qualified": True,
                "sales_exec": sales_reps[2],
                "book_slot_offset": -3,  # 3 days ago
                "book_status": BookingStatus.COMPLETED,
            },
            # Additional 27 Diverse & Realistic Indian Leads
            {
                "reference": "LD-58225", "name": "Mehul Prajapati", "phone": "+919825158225", "raw_phone": "9825158225",
                "email": "mehul.p@gmail.com", "source": LeadSource.WEBSITE, "project": project1, "bhk": "2 BHK",
                "budget_min": 6500000, "budget_max": 7500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.QUALIFIED,
                "score": 85, "is_qualified": True, "sales_exec": sales_reps[0], "book_slot_offset": 1, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58226", "name": "Deepak Bhatt", "phone": "+919825158226", "raw_phone": "9825158226",
                "email": "deepak.bhatt@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project2, "bhk": "3 BHK",
                "budget_min": 10500000, "budget_max": 12000000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 95, "is_qualified": True, "sales_exec": sales_reps[3], "book_slot_offset": 3, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58227", "name": "Sheetal Raval", "phone": "+919825158227", "raw_phone": "+91 98251 58227",
                "email": "sheetal.raval@outlook.com", "source": LeadSource.SOCIAL_MEDIA, "project": project1, "bhk": "3 BHK",
                "budget_min": 8500000, "budget_max": 9500000, "timeline": "3-6 months", "status": LeadStatus.NEW,
                "score": 60, "is_qualified": False, "sales_exec": None, "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58228", "name": "Sanjay Dave", "phone": "+919825158228", "raw_phone": "9825158228",
                "email": "dave.sanjay@gmail.com", "source": LeadSource.HOARDING, "project": project1, "bhk": "2 BHK",
                "budget_min": 5000000, "budget_max": 5800000, "timeline": "6+ months", "status": LeadStatus.NOT_INTERESTED,
                "score": 25, "is_qualified": False, "sales_exec": sales_reps[4], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58229", "name": "Bhavna Trivedi", "phone": "+919825158229", "raw_phone": "09825158229",
                "email": "bhavna.t@gmail.com", "source": LeadSource.WEBSITE, "project": project2, "bhk": "3 BHK",
                "budget_min": 11000000, "budget_max": 12500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.HUMAN_FOLLOWUP,
                "score": 90, "is_qualified": True, "sales_exec": sales_reps[1], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58230", "name": "Pranav Kapadia", "phone": "+919825158230", "raw_phone": "9825158230",
                "email": "pranav.k@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project1, "bhk": "2 BHK",
                "budget_min": 7000000, "budget_max": 8000000, "timeline": "1-3 months", "status": LeadStatus.VISITED,
                "score": 80, "is_qualified": True, "sales_exec": sales_reps[2], "book_slot_offset": -2, "book_status": BookingStatus.COMPLETED
            },
            {
                "reference": "LD-58231", "name": "Ananya Barot", "phone": "+919825158231", "raw_phone": "+919825158231",
                "email": "ananya.barot@yahoo.com", "source": LeadSource.SOCIAL_MEDIA, "project": project2, "bhk": "2 BHK",
                "budget_min": 8500000, "budget_max": 9200000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 85, "is_qualified": True, "sales_exec": sales_reps[5], "book_slot_offset": 4, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58232", "name": "Ketan Vora", "phone": "+919825158232", "raw_phone": "9825158232",
                "email": "ketan.vora@gmail.com", "source": LeadSource.MANUAL_ENTRY, "project": project2, "bhk": "3 BHK",
                "budget_min": 10000000, "budget_max": 11500000, "timeline": "1-3 months", "status": LeadStatus.QUALIFIED,
                "score": 85, "is_qualified": True, "sales_exec": sales_reps[6], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58233", "name": "Geeta Rajput", "phone": "+919825158233", "raw_phone": "9825158233",
                "email": "geeta.rajput@gmail.com", "source": LeadSource.HOARDING, "project": project1, "bhk": "2 BHK",
                "budget_min": 6800000, "budget_max": 7500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 80, "is_qualified": True, "sales_exec": sales_reps[7], "book_slot_offset": 5, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58234", "name": "Rameshchandra Soni", "phone": "+919825158234", "raw_phone": "9825158234",
                "email": "ramesh.soni@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project2, "bhk": "3 BHK",
                "budget_min": 11500000, "budget_max": 12500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISITED,
                "score": 95, "is_qualified": True, "sales_exec": sales_reps[0], "book_slot_offset": -4, "book_status": BookingStatus.COMPLETED
            },
            {
                "reference": "LD-58235", "name": "Pooja Makwana", "phone": "+919825158235", "raw_phone": "9825158235",
                "email": "pooja.makwana@gmail.com", "source": LeadSource.WEBSITE, "project": project1, "bhk": "2 BHK",
                "budget_min": 6500000, "budget_max": 7200000, "timeline": "3-6 months", "status": LeadStatus.NEW,
                "score": 50, "is_qualified": False, "sales_exec": None, "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58236", "name": "Haresh Thakkar", "phone": "+919825158236", "raw_phone": "+91 9825158236",
                "email": "haresh.t@gmail.com", "source": LeadSource.SOCIAL_MEDIA, "project": project2, "bhk": "2 BHK",
                "budget_min": 9000000, "budget_max": 9500000, "timeline": "1-3 months", "status": LeadStatus.CONTACTED,
                "score": 75, "is_qualified": True, "sales_exec": sales_reps[8], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58237", "name": "Alpa Gadhvi", "phone": "+919825158237", "raw_phone": "9825158237",
                "email": "alpa.g@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project1, "bhk": "3 BHK",
                "budget_min": 8500000, "budget_max": 9200000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 90, "is_qualified": True, "sales_exec": sales_reps[9], "book_slot_offset": 2, "book_status": BookingStatus.CANCELLED
            },
            {
                "reference": "LD-58238", "name": "Vimal Somani", "phone": "+919825158238", "raw_phone": "09825158238",
                "email": "vimal.somani@gmail.com", "source": LeadSource.HOARDING, "project": project2, "bhk": "3 BHK",
                "budget_min": 10500000, "budget_max": 11500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 90, "is_qualified": True, "sales_exec": sales_reps[10], "book_slot_offset": 6, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58239", "name": "Tarun Kothari", "phone": "+919825158239", "raw_phone": "9825158239",
                "email": "tarun.kothari@gmail.com", "source": LeadSource.WEBSITE, "project": project1, "bhk": "2 BHK",
                "budget_min": 6500000, "budget_max": 7000000, "timeline": "1-3 months", "status": LeadStatus.QUALIFIED,
                "score": 80, "is_qualified": True, "sales_exec": sales_reps[3], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58240", "name": "Ruchir Sanghvi", "phone": "+919825158240", "raw_phone": "9825158240",
                "email": "ruchir.s@gmail.com", "source": LeadSource.SOCIAL_MEDIA, "project": project2, "bhk": "3 BHK",
                "budget_min": 10000000, "budget_max": 11000000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISITED,
                "score": 90, "is_qualified": True, "sales_exec": sales_reps[4], "book_slot_offset": -5, "book_status": BookingStatus.COMPLETED
            },
            {
                "reference": "LD-58241", "name": "Dipti Chokshi", "phone": "+919825158241", "raw_phone": "9825158241",
                "email": "dipti.chokshi@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project1, "bhk": "3 BHK",
                "budget_min": 8800000, "budget_max": 9600000, "timeline": "1-3 months", "status": LeadStatus.VISIT_BOOKED,
                "score": 85, "is_qualified": True, "sales_exec": sales_reps[1], "book_slot_offset": 3, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58242", "name": "Nirav Shukla", "phone": "+919825158242", "raw_phone": "9825158242",
                "email": "nirav.shukla@gmail.com", "source": LeadSource.WEBSITE, "project": project2, "bhk": "2 BHK",
                "budget_min": 8500000, "budget_max": 9200000, "timeline": "3-6 months", "status": LeadStatus.NEW,
                "score": 60, "is_qualified": False, "sales_exec": None, "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58243", "name": "Manish Zaveri", "phone": "+919825158243", "raw_phone": "9825158243",
                "email": "manish.zaveri@gmail.com", "source": LeadSource.HOARDING, "project": project2, "bhk": "3 BHK",
                "budget_min": 11000000, "budget_max": 12000000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 95, "is_qualified": True, "sales_exec": sales_reps[2], "book_slot_offset": 7, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58244", "name": "Urvi Vyas", "phone": "+919825158244", "raw_phone": "9825158244",
                "email": "urvi.vyas@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project1, "bhk": "2 BHK",
                "budget_min": 6500000, "budget_max": 7500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISITED,
                "score": 85, "is_qualified": True, "sales_exec": sales_reps[0], "book_slot_offset": -6, "book_status": BookingStatus.COMPLETED
            },
            {
                "reference": "LD-58245", "name": "Chetan Modi", "phone": "+919825158245", "raw_phone": "9825158245",
                "email": "chetan.modi@gmail.com", "source": LeadSource.SOCIAL_MEDIA, "project": project1, "bhk": "3 BHK",
                "budget_min": 8500000, "budget_max": 9000000, "timeline": "1-3 months", "status": LeadStatus.LOST,
                "score": 40, "is_qualified": False, "sales_exec": sales_reps[5], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58246", "name": "Darshan Shah", "phone": "+919825158246", "raw_phone": "9825158246",
                "email": "darshan.shah@gmail.com", "source": LeadSource.WEBSITE, "project": project2, "bhk": "2 BHK",
                "budget_min": 8500000, "budget_max": 9500000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISIT_BOOKED,
                "score": 85, "is_qualified": True, "sales_exec": sales_reps[6], "book_slot_offset": 1, "book_status": BookingStatus.CONFIRMED
            },
            {
                "reference": "LD-58247", "name": "Ila Oza", "phone": "+919825158247", "raw_phone": "9825158247",
                "email": "ila.oza@gmail.com", "source": LeadSource.HOARDING, "project": project1, "bhk": "2 BHK",
                "budget_min": 6500000, "budget_max": 7000000, "timeline": "1-3 months", "status": LeadStatus.CONTACTED,
                "score": 75, "is_qualified": True, "sales_exec": sales_reps[7], "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58248", "name": "Brijesh Panchal", "phone": "+919825158248", "raw_phone": "9825158248",
                "email": "brijesh.p@gmail.com", "source": LeadSource.PROPERTY_PORTAL, "project": project2, "bhk": "3 BHK",
                "budget_min": 11500000, "budget_max": 12000000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.VISITED,
                "score": 90, "is_qualified": True, "sales_exec": sales_reps[8], "book_slot_offset": -1, "book_status": BookingStatus.COMPLETED
            },
            {
                "reference": "LD-58249", "name": "Varsha Vaghela", "phone": "+919825158249", "raw_phone": "9825158249",
                "email": "varsha.v@gmail.com", "source": LeadSource.SOCIAL_MEDIA, "project": project1, "bhk": "3 BHK",
                "budget_min": 8500000, "budget_max": 9200000, "timeline": "3-6 months", "status": LeadStatus.NEW,
                "score": 55, "is_qualified": False, "sales_exec": None, "book_slot_offset": None, "book_status": None
            },
            {
                "reference": "LD-58250", "name": "Yogesh Patel", "phone": "+919825158250", "raw_phone": "9825158250",
                "email": "yogesh.patel@gmail.com", "source": LeadSource.WEBSITE, "project": project2, "bhk": "3 BHK",
                "budget_min": 10500000, "budget_max": 11800000, "timeline": "Immediate (0-1 mo)", "status": LeadStatus.HUMAN_FOLLOWUP,
                "score": 90, "is_qualified": True, "sales_exec": sales_reps[9], "book_slot_offset": None, "book_status": None
            },
        ]

        created_leads = []
        for l_data in leads_data:
            # Simulate historical touchpoints
            created_time = now - timedelta(days=abs(l_data.get("book_slot_offset") or 3) + 2)
            lead = Lead(
                lead_reference=l_data["reference"],
                full_name=l_data["name"],
                normalized_phone=l_data["phone"],
                raw_phone=l_data["raw_phone"],
                email=l_data["email"],
                source=l_data["source"],
                preferred_project_id=l_data["project"].id,
                preferred_bhk=l_data["bhk"],
                budget_min=l_data["budget_min"],
                budget_max=l_data["budget_max"],
                preferred_location="Ahmedabad",
                buying_timeline=l_data["timeline"],
                purchase_reason="Self Use",
                status=l_data["status"],
                qualification_score=l_data["score"],
                is_qualified=l_data["is_qualified"],
                assigned_executive_id=l_data["sales_exec"].id if l_data["sales_exec"] else None,
                consent_status=True,
                first_contact_at=created_time + timedelta(minutes=4),  # sub-5-minute AI contact!
                last_contact_at=now - timedelta(hours=2),
                created_at=created_time
            )
            db.add(lead)
            created_leads.append((lead, l_data))

        db.commit()

        # 6. Create Bookings and Conversations for Leads
        for lead, l_data in created_leads:
            # Attach a realistic conversation
            conv = Conversation(
                lead_id=lead.id,
                session_token=f"sess-{lead.lead_reference.lower()}",
                preferred_language="en",
                is_flagged=l_data["status"] == LeadStatus.HUMAN_FOLLOWUP,
                flagged_reason="Buyer demanded custom 15% discount not on approved price sheet" if l_data["status"] == LeadStatus.HUMAN_FOLLOWUP else None,
                is_handed_off=l_data["status"] == LeadStatus.HUMAN_FOLLOWUP
            )
            db.add(conv)
            db.flush()

            # Realistic messages
            m1 = Message(
                conversation_id=conv.id,
                sender_type="assistant",
                content=f"Namaste {lead.full_name}! Welcome to Company A properties in Ahmedabad. Are you looking for a 2 BHK or 3 BHK apartment?",
                language="en",
                created_at=lead.created_at
            )
            m2 = Message(
                conversation_id=conv.id,
                sender_type="buyer",
                content=f"Hello, I am interested in {lead.preferred_bhk} at {l_data['project'].name}. What is the price and carpet area?",
                language="en",
                created_at=lead.created_at + timedelta(minutes=1)
            )
            m3 = Message(
                conversation_id=conv.id,
                sender_type="assistant",
                content=f"{l_data['project'].name} offers approved {lead.preferred_bhk} configurations with prices starting around ₹{lead.budget_min/100000:.0f} Lakh. The project is RERA approved ({l_data['project'].rera_number}). Would you like to schedule a site visit?",
                language="en",
                created_at=lead.created_at + timedelta(minutes=2)
            )
            db.add_all([m1, m2, m3])

            # If booking offset is present, attach booking and lock slot
            offset = l_data.get("book_slot_offset")
            if offset is not None:
                target_day = (base_date + timedelta(days=offset)).strftime("%Y-%m-%d 11:00")
                slot = slot_map.get((l_data["project"].id, target_day))
                if slot:
                    b_status = l_data["book_status"]
                    booking = Booking(
                        booking_reference=f"BK-{lead.lead_reference.split('-')[1]}",
                        lead_id=lead.id,
                        project_id=l_data["project"].id,
                        slot_id=slot.id,
                        assigned_salesperson_id=l_data["sales_exec"].id if l_data["sales_exec"] else sales_reps[0].id,
                        status=b_status,
                        notes=f"Buyer interested in {lead.preferred_bhk}. Site visit scheduled.",
                        confirmed_at=lead.created_at + timedelta(minutes=5),
                        cancelled_at=now if b_status == BookingStatus.CANCELLED else None,
                        cancellation_reason="Buyer rescheduled to next month" if b_status == BookingStatus.CANCELLED else None
                    )
                    db.add(booking)
                    if b_status != BookingStatus.CANCELLED:
                        slot.booked_count += 1

            # If human follow-up, create handoff record
            if l_data["status"] == LeadStatus.HUMAN_FOLLOWUP:
                handoff = Handoff(
                    lead_id=lead.id,
                    conversation_id=conv.id,
                    assigned_to_user_id=lead.assigned_executive_id or sales_reps[0].id,
                    reason="Buyer requested negotiation outside approved fact sheet",
                    priority="HIGH",
                    structured_summary=(
                        f"Buyer Name: {lead.full_name}\n"
                        f"Phone: {lead.normalized_phone}\n"
                        f"Project: {l_data['project'].name}\n"
                        f"Configuration: {lead.preferred_bhk}\n"
                        f"Budget: ₹{lead.budget_min/100000:.0f}L - ₹{lead.budget_max/100000:.0f}L\n"
                        f"Timeline: {lead.buying_timeline}\n"
                        f"Escalation Reason: Requested unapproved 15% discount\n"
                        f"Recommended Next Action: Call buyer directly to discuss standard festive payment schedule"
                    ),
                    recommended_action="Call buyer directly to discuss standard festive payment schedule",
                    status="PENDING"
                )
                db.add(handoff)

        db.commit()

        # 7. Create Monthly Marketing Spend records (₹30 Lakh total spend)
        current_month = "2026-11"
        spends = [
            MarketingSpend(project_id=project1.id, source=LeadSource.PROPERTY_PORTAL, month_year=current_month, spend_amount=600000),
            MarketingSpend(project_id=project2.id, source=LeadSource.PROPERTY_PORTAL, month_year=current_month, spend_amount=600000),
            MarketingSpend(project_id=project1.id, source=LeadSource.SOCIAL_MEDIA, month_year=current_month, spend_amount=500000),
            MarketingSpend(project_id=project2.id, source=LeadSource.SOCIAL_MEDIA, month_year=current_month, spend_amount=500000),
            MarketingSpend(project_id=project1.id, source=LeadSource.HOARDING, month_year=current_month, spend_amount=250000),
            MarketingSpend(project_id=project2.id, source=LeadSource.HOARDING, month_year=current_month, spend_amount=250000),
            MarketingSpend(project_id=project1.id, source=LeadSource.WEBSITE, month_year=current_month, spend_amount=150000),
            MarketingSpend(project_id=project2.id, source=LeadSource.WEBSITE, month_year=current_month, spend_amount=150000),
        ]
        db.add_all(spends)
        db.commit()

        print(f"Successfully seeded database: {len(users)} users, 2 projects, {len(facts)} facts, {len(created_leads)} leads, {len(slots_to_add)} slots.")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
