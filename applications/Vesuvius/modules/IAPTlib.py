
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
          ## Illegal State!
          proj['image'] = None
          proj['imageAlt'] = None
    return projectSet

def searchProjects(terms, db):
    """
    Searches the database based on project title, project descriptions and keywords for a project. Will only return
    project in state 'open'
    :param terms: search terms
    :param db: the database
    :return: projects matching the search
    """
    splitTerms = terms.split(' ')
    titleQuery = (db.projects.title.contains(splitTerms, all=True))
    descriptionQuery = (db.projects.description.contains(splitTerms, all=True))
    keywordsQuery = (db.keywords.keyword.contains(splitTerms, all=False) &
                    (db.keywords.id == db.projectKeywords.keywordID) &
                    (db.projects.id == db.projectKeywords.projectID)
                    )
    openQuery = (db.projects.state == 'open')

    if db(db.projectKeywords.id > 0).count() > 0:
        query = ((titleQuery | descriptionQuery | keywordsQuery) & openQuery)
    else:
        query = ((titleQuery | descriptionQuery) & openQuery)

    results = db(query).select(db.projects.id, db.projects.title, db.projects.description, distinct=True)
    return results