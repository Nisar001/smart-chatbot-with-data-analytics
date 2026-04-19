CREATE INDEX IF NOT EXISTS idx_datasets_owner_status ON datasets (owner_id, status);
CREATE INDEX IF NOT EXISTS idx_conversations_user_dataset ON conversations (user_id, dataset_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_role ON messages (conversation_id, role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);
