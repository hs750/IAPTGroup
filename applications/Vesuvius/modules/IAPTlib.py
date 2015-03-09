
### DEVELOPER NOTE:
# If you edit a web2py module (anything in the /modules/ folder) you must restart
# web2py completely for changes to come through.
# Refreshing the page or restarting the server is not enough.

def addImagesToProjects(projectSet, db):
    """
    Adds the image of the first document of a project to a project to act as the projects image
    :param projectSet: A set of projects (as returned from a db query)
    :param db: The database
    :return: projectSet with every project in the set having an image.
    """
    for proj in projectSet:
        docImg = db(db.documents.projectID == proj.id).select(db.documents.image, db.documents.title)
        if docImg:
          proj['image'] = docImg[0].image
          proj['imageAlt'] = 'Image of: ' + docImg[0].title
        else:
          ## Should not happen, can remove this when we are confident this won't happen.
          print("Error: Project without a document image exists!")
    return projectSet

# def searchProjects(terms, db):
#     splitTerms = terms.split(',')
#     results = db(((db.projects.title.contains(splitTerms)) | (db.projects.description.contains(splitTerms)) |
#                  (db.keywords.keyword.contains(splitTerms, all=False) &
#                   (db.keywords.id == db.projectKeywords.keywordID) &
#                   (db.projects.id == db.projectKeywords.projectID)
#                  )) & (db.projects.state == 'open')
#                 ).select(db.projects.id, db.projects.title, db.projects.description)
#     return results

# This is a quick and dirty search workaround as the above search was returning nothing for me.
# Searches only project titles.
def searchProjects(terms, db):
    query = db.projects.title.like('%'+terms+'%')
    return db(query).select(db.projects.title, db.projects.description, db.projects.id)