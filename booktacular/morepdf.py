#!/usr/bin/env python
from __future__ import print_function
import sys
import fitz  # PyMuPDF
import argparse
import os


class MorePDF:
    def __init__(self):
        self.doc = None

    def load(self, path):
        """Load the PDF document."""
        try:
            self.doc = fitz.open(path)
        except Exception as e:
            print("Failed to open document: %s" % e)
            sys.exit(1)

    def replace_text_in_pdf(self, old, new=None):
        """
        Replace or find text in a PDF file.

        Args:
            old (str): The old string to be replaced or found.
            new (str, optional): The new string to replace the old string with.
                                 If None, the function only prints occurrences.
        """
        if self.doc is None:
            print("Document not loaded.")
            return

        total_replaced = 0
        # Iterate through the pages and search for the old string
        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            text_instances = page.search_for(old)

            block_replaced = 0
            for inst in text_instances:
                if new is None:
                    # If new is None, just print the occurrences
                    print("Page %d:" % page_num)
                    print(page.get_textbox(inst))
                else:
                    # Add "whiteout" then annotate over it:
                    page.add_redact_annot(inst, new, fill=(.985, .967, .94))
                    # ^ color is 1-, 3-, or 4-long tuple, each component
                    #   having the range 0 to 1.
                    # TODO: make color configurable
                    page.apply_redactions()
                    block_replaced += 1

            total_replaced += block_replaced

        if new is not None:
            print("%d replacement(s) complete" % total_replaced)

    def save(self, path, suffix=None):
        """Save the modified PDF file."""
        if self.doc is None:
            print("Document not loaded.")
            return

        output_path = os.path.splitext(path)[0]
        if suffix is not None:
            output_path += "-%s.pdf" % suffix
        else:
            output_path += ".pdf"

        self.doc.save(output_path)
        self.doc.close()
        print("Modified PDF saved as %s" % output_path)


def main():
    parser = argparse.ArgumentParser(description="PDF text replacement tool.")
    parser.add_argument("path", help="Path to the PDF file")
    parser.add_argument("-f", "--find", required=True, help="Text to find")
    parser.add_argument("-r", "--replace", help="Text to replace with")

    args = parser.parse_args()

    # Initialize the PDF editor
    pdf_editor = MorePDF()
    pdf_editor.load(args.path)

    # Perform the find or replace operation
    if args.replace:
        pdf_editor.replace_text_in_pdf(args.find, args.replace)
    else:
        pdf_editor.replace_text_in_pdf(args.find, None)

    # Save the document only if replacement is performed
    if args.replace:
        pdf_editor.save(args.path, suffix=args.replace)


if __name__ == "__main__":
    sys.exit(main())
