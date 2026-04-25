from email.email_reader import fetch_resumes
from email.resume_parser import extract_resume_text


def main():
    files = fetch_resumes()

    if not files:
        print("\nNo new resumes found.")
        return

    for file in files:
        print("\n==============================")
        print("Resume File:", file)

        text = extract_resume_text(file)

        if text.strip():
            print("\nResume Preview:")
            print(text[:500])
        else:
            print("No text extracted (possibly scanned PDF).")


if __name__ == "__main__":
    main()