import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
export const workspaces=sqliteTable('workspaces',{
 owner:text('owner').primaryKey(),
 revision:integer('revision').notNull().default(0),
 state:text('state').notNull(),
});
