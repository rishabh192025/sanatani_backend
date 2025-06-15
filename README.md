# sanatani_backend


How this maps to your Admin UI:
Books: Content where content_type == BOOK.
Audiobooks: Content where content_type == AUDIO_CONTENT (and possibly sub_type == GENERAL or a specific AUDIOBOOK sub_type if you add one, or linked to a BOOK content type).
Stories: Content where sub_type == STORY (could be content_type == ARTICLE or content_type == AUDIO_CONTENT). The admin UI would filter by sub_type.
Teachings: Content where sub_type == TEACHING (could be content_type == ARTICLE, AUDIO_CONTENT, or VIDEO). The admin UI would filter by sub_type.
Collections: This requires implementing the Collection and CollectionItem models, schemas, CRUD, and API endpoints. This is a distinct piece of work.