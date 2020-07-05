import utils

from genreport import ReportGenerator


def test_regex():
    print(utils.extract_issues("PDFBOX-13 aPDFBOX-152b qweqweqweqweqwePDFBOX-173435345sdfa4", "PDFBOX"))
    print(utils.extract_revisions("Revision 123commit 5rhdrghfCommit 72 rev. 12312Rev.36Rev. 123r6453241"))
    print(
        utils.extract_revisions("Revision 123commit 5rhdrghfCommit 72 rev. 12312Rev.36Rev. 123r6453241", uniform=True))


def test_svn_url_construction():
    revisions = utils.extract_revisions("revision 1835045rev. 1835515   r1835516")
    for revision in revisions:
        print(utils.construct_svn_revision_url(revision))


# test_regex()
# test_svn_url_construction()
# print(utils.extract_urls("https://svn.apache.org/r1231331  https://svn.apache.or/ https://vk.com", filter_revisions=False))


# for filename in os.listdir("Projects/PDFBOX/URLs"):
#     with open(os.path.join("Projects/PDFBOX/URLs", filename), 'r') as file:
#         mailing_lists = utils.filter_mailing_list_urls(set(file.readlines()))
#         if len(mailing_lists) == 0:
#             continue
#         print(filename)
#         for ml in mailing_lists:
#             print(ml)
#         print()


issue_key = "PDFBOX-4908"
issue = utils.load_json("Projects/PDFBOX/Issues/PDFBOX-4908.json")
generator = ReportGenerator("PDFBOX", issue_key)
generator.generate_report()
