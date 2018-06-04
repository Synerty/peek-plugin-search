"""initial tables

Peek Plugin Database Migration Script

Revision ID: 53fccd56fa39
Revises: 
Create Date: 2018-06-03 14:18:15.583831

"""

# revision identifiers, used by Alembic.
revision = '53fccd56fa39'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import geoalchemy2


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('EncodedSearchIndexChunk',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chunkKey', sa.String(), nullable=False),
    sa.Column('encodedData', sa.LargeBinary(), nullable=False),
    sa.Column('encodedHash', sa.String(), nullable=False),
    sa.Column('lastUpdate', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'chunkKey'),
    schema='pl_search'
    )
    op.create_index('idx_EncodedSearchIndex_chunkKey', 'EncodedSearchIndexChunk', ['chunkKey'], unique=True, schema='pl_search')
    op.create_table('EncodedSearchObjectChunk',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chunkKey', sa.String(), nullable=False),
    sa.Column('encodedData', sa.LargeBinary(), nullable=False),
    sa.Column('encodedHash', sa.String(), nullable=False),
    sa.Column('lastUpdate', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'chunkKey'),
    schema='pl_search'
    )
    op.create_index('idx_EncodedSearchObject_chunkKey', 'EncodedSearchObjectChunk', ['chunkKey'], unique=True, schema='pl_search')
    op.create_table('SearchIndexCompilerQueue',
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('chunkKey', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'chunkKey'),
    schema='pl_search'
    )
    op.create_table('SearchObject',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('chunkKey', sa.String(), nullable=False),
    sa.Column('detailJson', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='pl_search'
    )
    op.create_index('idx_SearchObject_chunkKey', 'SearchObject', ['chunkKey'], unique=False, schema='pl_search')
    op.create_index('idx_SearchObject_keyword', 'SearchObject', ['key'], unique=True, schema='pl_search')
    op.create_table('SearchObjectCompilerQueue',
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('chunkKey', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'chunkKey'),
    schema='pl_search'
    )
    op.create_table('SearchPropertyTuple',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='pl_search'
    )
    op.create_table('Setting',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='pl_search'
    )
    op.create_table('SearchIndex',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chunkKey', sa.String(), nullable=False),
    sa.Column('keyword', sa.String(), nullable=False),
    sa.Column('propertyName', sa.String(), nullable=False),
    sa.Column('objectId', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['objectId'], ['pl_search.SearchObject.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='pl_search'
    )
    op.create_index('idx_SearchIndex_quick_query', 'SearchIndex', ['chunkKey', 'keyword', 'propertyName', 'objectId'], unique=True, schema='pl_search')
    op.create_table('SearchObjectRoute',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('objectId', sa.Integer(), nullable=False),
    sa.Column('importGroupHash', sa.String(), nullable=False),
    sa.Column('routeTitle', sa.String(), nullable=False),
    sa.Column('routePath', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['objectId'], ['pl_search.SearchObject.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    schema='pl_search'
    )
    op.create_index('idx_ObjectRoute_objectId', 'SearchObjectRoute', ['objectId'], unique=False, schema='pl_search')
    op.create_index('idx_ObjectRoute_routeTitle_importGroupHash', 'SearchObjectRoute', ['importGroupHash'], unique=False, schema='pl_search')
    op.create_index('idx_ObjectRoute_routeTitle_objectId', 'SearchObjectRoute', ['routeTitle', 'objectId'], unique=True, schema='pl_search')
    op.create_table('SettingProperty',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('settingId', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=50), nullable=False),
    sa.Column('type', sa.String(length=16), nullable=True),
    sa.Column('int_value', sa.Integer(), nullable=True),
    sa.Column('char_value', sa.String(), nullable=True),
    sa.Column('boolean_value', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['settingId'], ['pl_search.Setting.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='pl_search'
    )
    op.create_index('idx_SettingProperty_settingId', 'SettingProperty', ['settingId'], unique=False, schema='pl_search')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_SettingProperty_settingId', table_name='SettingProperty', schema='pl_search')
    op.drop_table('SettingProperty', schema='pl_search')
    op.drop_index('idx_ObjectRoute_routeTitle_objectId', table_name='SearchObjectRoute', schema='pl_search')
    op.drop_index('idx_ObjectRoute_routeTitle_importGroupHash', table_name='SearchObjectRoute', schema='pl_search')
    op.drop_index('idx_ObjectRoute_objectId', table_name='SearchObjectRoute', schema='pl_search')
    op.drop_table('SearchObjectRoute', schema='pl_search')
    op.drop_index('idx_SearchIndex_quick_query', table_name='SearchIndex', schema='pl_search')
    op.drop_table('SearchIndex', schema='pl_search')
    op.drop_table('Setting', schema='pl_search')
    op.drop_table('SearchPropertyTuple', schema='pl_search')
    op.drop_table('SearchObjectCompilerQueue', schema='pl_search')
    op.drop_index('idx_SearchObject_keyword', table_name='SearchObject', schema='pl_search')
    op.drop_index('idx_SearchObject_chunkKey', table_name='SearchObject', schema='pl_search')
    op.drop_table('SearchObject', schema='pl_search')
    op.drop_table('SearchIndexCompilerQueue', schema='pl_search')
    op.drop_index('idx_EncodedSearchObject_chunkKey', table_name='EncodedSearchObjectChunk', schema='pl_search')
    op.drop_table('EncodedSearchObjectChunk', schema='pl_search')
    op.drop_index('idx_EncodedSearchIndex_chunkKey', table_name='EncodedSearchIndexChunk', schema='pl_search')
    op.drop_table('EncodedSearchIndexChunk', schema='pl_search')
    # ### end Alembic commands ###