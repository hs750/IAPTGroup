
### DEVELOPER NOTE:
# If you edit a web2py module (anything in the /modules/ folder) you must
# restart web2py completely (the server must be restarted) for changes to come through.
# Refreshing the page is not enough.

def addImagesToProjects(projectSet, db):
    """
    Adds the image of the first document of a project to a project to act as the projects image
    :param projectSet: A set of projects (as returned from a db query)
    :param db: The database
    :return: projectSet with every project in the set having an image.
    """
    for proj in projectSet:
        docImg = db(db.documents.projectID == proj.id).select(db.documents.image, db.documents.title)
        proj['image'] = docImg[0].image
        proj['imageAlt'] = 'Image of: ' + docImg[0].title
    return projectSet