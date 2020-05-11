import utils


def test_regex():
    print(utils.extract_issues("PDFBOX-13 aPDFBOX-152b qweqweqweqweqwePDFBOX-173435345sdfa4", "PDFBOX"))
    print(utils.extract_revisions("Revision 123commit 5rhdrghfCommit 72 rev. 12312Rev.36Rev. 123r6453241"))


def test_svn_url_construction():
    revisions = utils.extract_revisions("revision 1835045rev. 1835515   r1835516")
    for revision in revisions:
        print(utils.construct_svn_revision_url(revision))


test_regex()
test_svn_url_construction()
