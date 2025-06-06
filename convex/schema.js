import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
    messages: defineTable({
        // Message identifiers
        messageId: v.string(), // from Surge API
        messageBody: v.optional(v.string()),
        accountId: v.string(),
        receivedAt: v.string(),

        // Contact information
        contactId: v.string(),
        contactPhoneNumber: v.string(),

        // Conversation information
        conversationId: v.string(),
        phoneNumberId: v.string(),
        phoneNumber: v.string(),
        phoneNumberType: v.string(),

        // Timestamps
        createdAt: v.number(),
    }).index("by_message_id", ["messageId"])
        .index("by_contact_id", ["contactId"])
        .index("by_conversation_id", ["conversationId"])
        .index("by_phone_number", ["contactPhoneNumber"]),

    attachments: defineTable({
        // Link to message
        messageId: v.string(), // Surge message ID
        convexMessageId: v.id("messages"), // Reference to our messages table

        // Attachment data
        attachmentId: v.string(), // from Surge API
        type: v.string(),
        url: v.string(),

        // Classification
        classification: v.optional(v.string()),

        // Timestamps
        createdAt: v.number(),
    }).index("by_message_id", ["messageId"])
        .index("by_convex_message_id", ["convexMessageId"]),

    conversions: defineTable({
        // Link to message
        messageId: v.id("messages"), // Reference to our messages table
        convexMessageId: v.id("messages"), // Reference to our messages table

        // Conversion data
        signedUrl: v.string(), // After Image Generation, Signed URL following upload to S3
        s3Key: v.string(), // After Image Generation, S3 Key following upload to S3
        
        // Timestamps
        createdAt: v.number(),
    }).index("by_message_id", ["messageId"])
        .index("by_convex_message_id", ["convexMessageId"])
}); 