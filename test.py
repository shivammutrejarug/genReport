import utils


def test_regex():
    print(utils.extract_issues("PDFBOX-13 aPDFBOX-152b qweqweqweqweqwePDFBOX-173435345sdfa4", "PDFBOX"))
    print(utils.extract_revisions("Revision 123commit 5rhdrghfCommit 72 rev. 12312Rev.36Rev. 123r6453241"))


def test_first_number_extraction():
    string = "jnfgjkn   7 12355123nvj6453kjdgf99"
    print(utils.extract_numbers(string))


test_regex()
test_first_number_extraction()
