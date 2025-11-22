from app import create_app, db
from app.models import Customer, CustomerLabel

def read_customers_with_labels(limit=10):
    app = create_app()
    with app.app_context():
        # Query customers left outer joined with labels
        query = (
            db.session.query(Customer, CustomerLabel)
            .outerjoin(CustomerLabel, Customer.id == CustomerLabel.id)
            .limit(limit)
        )
        
        for customer, label in query.all():
            print(f"Customer ID: {customer.id}")
            print(f"  Age: {customer.age}, REST_AVG_CUR: {customer.rest_avg_cur}")
            if label:
                print(f"  Target: {label.target}")
            else:
                print("  Target: (unlabelled)")
            print("-" * 30)

if __name__ == "__main__":
    read_customers_with_labels()
