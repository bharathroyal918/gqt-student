import os
import sys

import psycopg


def main():
    regions = [
        "ap-south-1",  # Mumbai / India
        "ap-southeast-1",  # Singapore
        "ap-northeast-1",  # Tokyo
        "us-east-1",  # N. Virginia
        "us-west-1",  # N. California
        "eu-central-1",  # Frankfurt
        "eu-west-1",  # Ireland
        "eu-west-2",  # London
        "ca-central-1",  # Canada
        "sa-east-1",  # Sao Paulo
        "ap-southeast-2",  # Sydney
    ]

    password = os.environ.get("SUPABASE_DB_PASSWORD", "")
    user = os.environ.get("SUPABASE_DB_USER", "")

    if not password or not user:
        print(
            "Please set SUPABASE_DB_USER and SUPABASE_DB_PASSWORD in your environment to test connectivity."
        )
        sys.exit(1)

    found = None
    for r in regions:
        host = f"aws-0-{r}.pooler.supabase.com"
        print(f"Trying {r} -> {host} ...")
        try:
            conn = psycopg.connect(
                host=host,
                port=6543,
                dbname="postgres",
                user=user,
                password=password,
                sslmode="require",
                connect_timeout=4,
            )
            print(f">>> SUCCESS! Connected to Supabase in region [{r}]! <<<")
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                print("PostgreSQL version:", cur.fetchone()[0])
            conn.close()
            found = r
            break
        except psycopg.Error as e:
            print(f"Failed on {r}: {e}")

    if found:
        print("\nYour correct DATABASE_URL is:")
        print(
            f"postgresql://{user}:[YOUR-PASSWORD]@aws-0-{found}.pooler.supabase.com:6543/postgres?sslmode=require"
        )
    else:
        print(
            "\nCould not connect. Please verify your Supabase region or password in dashboard."
        )


if __name__ == "__main__":
    main()
