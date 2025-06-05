import { v } from "convex/values";
import { mutation } from "./_generated/server";

// Mutation to store a complete message with attachments
export const storeMessage = mutation({
    args: {
        // Message identifiers
        messageId: v.string(),
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

        // Attachments
        attachments: v.array(v.object({
            attachmentId: v.string(),
            type: v.string(),
            url: v.string(),
        })),
    },
    handler: async (ctx, args) => {
        // Store the main message
        const messageDocId = await ctx.db.insert("messages", {
            messageId: args.messageId,
            messageBody: args.messageBody,
            accountId: args.accountId,
            receivedAt: args.receivedAt,
            contactId: args.contactId,
            contactPhoneNumber: args.contactPhoneNumber,
            conversationId: args.conversationId,
            phoneNumberId: args.phoneNumberId,
            phoneNumber: args.phoneNumber,
            phoneNumberType: args.phoneNumberType,
            createdAt: Date.now(),
        });

        // Store attachments if any
        const attachmentIds = [];
        for (const attachment of args.attachments) {
            const attachmentDocId = await ctx.db.insert("attachments", {
                messageId: args.messageId,
                convexMessageId: messageDocId,
                attachmentId: attachment.attachmentId,
                type: attachment.type,
                url: attachment.url,
                createdAt: Date.now(),
            });
            attachmentIds.push(attachmentDocId);
        }

        return {
            messageId: messageDocId,
            attachmentIds: attachmentIds,
            success: true,
        };
    },
});
