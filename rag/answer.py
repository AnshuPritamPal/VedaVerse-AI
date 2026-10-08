
from .rag import generate_answer


def main():
    print("\n" + "=" * 55)
    print("          🪷 VEDAVERSE AI 🪷")
    print("=" * 55)

    print(
        "\nExplore spiritual wisdom through "
        "the teachings of the Bhagavad Gita."
    )
    print("\nType 'exit' to quit the application.")

    while True:
        question = input(
            "\nAsk VedaVerse AI a question: "
        ).strip()

        if question.lower() in ("exit", "quit"):
            print("\nThank you for using VedaVerse AI! 🪷")
            break

        if not question:
            print("\nPlease enter a valid question.")
            continue

        print("\nSearching the scriptures...")
        print("Generating your answer...\n")

        try:
            result = generate_answer(question)

        except Exception as error:
            print("\nSomething went wrong:")
            print(error)
            continue

        print("=" * 55)
        print("             VEDAVERSE AI'S ANSWER")
        print("=" * 55)

        print("\n" + result.get("answer", ""))

        # Display references
        references = result.get("references", [])

        if references:
            print("\nReferences:")
            for reference in references:
                print(f"- {reference}")
        else:
            print(
                "\nNo verified references were returned."
            )

        # Display complete retrieved scripture passages
        verses = result.get("verses", [])

        if verses:
            print("\n" + "=" * 55)
            print("       RELEVANT SCRIPTURE PASSAGES")
            print("=" * 55)

            for verse in verses:
                print("\n" + "-" * 55)
                print(f"🪷 {verse.get('reference', 'Unknown reference')}")
                print("-" * 55)

                if verse.get("sanskrit"):
                    print("\nSanskrit:")
                    print(verse["sanskrit"])

                if verse.get("transliteration"):
                    print("\nTransliteration:")
                    print(verse["transliteration"])

                if verse.get("word_for_word"):
                    print("\nWord-for-word:")
                    print(verse["word_for_word"])

                if verse.get("translation"):
                    print("\nTranslation:")
                    print(verse["translation"])

                if verse.get("purport"):
                    print("\nPurport:")
                    print(verse["purport"])

        # Display citation validation status
        print("\n" + "-" * 55)

        if result.get("validation_passed", False):
            print("Citation validation passed.")
        else:
            print(
                "WARNING: Some citations could not be "
                "matched to the retrieved full verses."
            )

        print("=" * 55)


if __name__ == "__main__":
    main()
