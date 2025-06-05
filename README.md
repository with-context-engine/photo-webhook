# Modal Deployment Guide for Memento Surge Webhooks

## Prerequisites

1. **Modal account**: Sign up at [modal.com](https://modal.com)
2. **Modal CLI**: Install with `pip install modal`
3. **Authentication**: Run `modal setup` to authenticate

## Setup Secrets

Create a Modal secret with your environment variables:

```bash
modal secret create memento-secrets \
  CONVEX_URL="https://your-deployment-name.convex.cloud" \
  SURGE_WEBHOOK_SECRET="your_webhook_secret_from_surge_dashboard"
```

## Deploy

### Development deployment (with live reloading):
```bash
modal serve src/memento/webhooks.py
```

### Production deployment:
```bash
modal deploy src/memento/webhooks.py
```

## Webhook URL

After deployment, Modal will provide you with a URL like:
```
https://your-workspace--memento-surge-webhooks-webhook-application-dev.modal.run
```

Your webhook endpoint will be:
```
https://your-workspace--memento-surge-webhooks-webhook-application-dev.modal.run/webhooks/surge
```

## Configure Surge

1. Go to your Surge dashboard
2. Navigate to Webhooks settings
3. Add the Modal webhook URL
4. Select "message.received" events
5. Save the webhook configuration

## Features

- ✅ **Auto-scaling**: Modal handles traffic spikes automatically
- ✅ **Signature validation**: Secure webhook verification
- ✅ **Structured logging**: Detailed message information
- ✅ **Health checks**: `/` endpoint for monitoring
- ✅ **Error handling**: Proper HTTP status codes
- ✅ **Ready for Convex**: Placeholder function for database integration

## Monitoring

- Check logs in Modal dashboard
- Use the health check endpoint for uptime monitoring
- Monitor function calls and performance metrics

## Next Steps

- Implement the `store_message_in_convex()` function
- Add more webhook event types as needed
- Set up monitoring and alerting 