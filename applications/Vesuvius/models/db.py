from gluon.tools import Auth

db = DAL('sqlite://IAPT_DB.db')

auth = Auth(db) #TODO Dave to sort authentication
auth.define_tables(username=True,signature=False)

# System State Constants
projectStates = ['open', 'closed']
documentStates = ['open', 'completed']
contributionStates = ['pending', 'accepted', 'rejected']

db.define_table(
    'projects',
    Field('title', 'string', requires=IS_NOT_EMPTY()),
    Field('description', 'text'),
    Field('state', 'string', writable=False, readable=False),
    Field('userID', db.auth_user, writable=False, readable=False)
)

requirementTypes = ['Short Text', 'Long Text', 'Date', 'Number']
db.define_table(
    'requirements',
    Field('name', 'string', requires=IS_NOT_EMPTY()),
    Field('type', 'string', requires=IS_IN_SET(requirementTypes), default=requirementTypes[0]),
    Field('projectID', db.projects)
)

db.define_table(
    'documents',
    Field('title', 'string'),
    Field('description', 'text', requires=IS_NOT_EMPTY()),
    Field('image', 'upload', requires=[IS_IMAGE(), IS_NOT_EMPTY()]),
    Field('state', 'string'),
    Field('projectID', db.projects)
)

db.define_table(
    'contributions',
    Field('content', 'text'),
    Field('state', 'string'),
    Field('userID', db.auth_user),
    Field('documentID', db.documents),
    Field('requirementID', db.requirements)
)

db.define_table(
    'keywords',
    Field('keyword', 'string', unique=True)
)

db.define_table(
    'projectKeywords',
    Field('keywordID', db.keywords),
    Field('projectID', db.projects)
)
