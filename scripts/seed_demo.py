"""Upload sample invoices and print their final pipeline statuses."""

import time

import httpx

API_URL = "http://localhost:8000"
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def main() -> None:
    invoice_ids = []
    with httpx.Client(base_url=API_URL, timeout=30) as client:
        for number in range(1, 3):
            response = client.post(
                "/invoices",
                files={"file": (f"demo-{number}.pdf", PDF, "application/pdf")},
            )
            response.raise_for_status()
            invoice_id = response.json()["id"]
            invoice_ids.append(invoice_id)
            print(f"Uploaded {invoice_id}")

        pending = set(invoice_ids)
        for _ in range(60):
            invoices = {item["id"]: item for item in client.get("/invoices").json()}
            for invoice_id in list(pending):
                status = invoices.get(invoice_id, {}).get("status", "UNKNOWN")
                if status not in {"PENDING", "QUEUED"}:
                    print(f"{invoice_id}: {status}")
                    pending.remove(invoice_id)
            if not pending:
                return
            time.sleep(2)
        print(f"Timed out waiting for: {', '.join(sorted(pending))}")


if __name__ == "__main__":
    main()
