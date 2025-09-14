from fastapi import Depends, Header, HTTPException, status
import os

def get_configured_token() -> str:
    """
    Load the API token from the environment.
    Fails closed if not configured.
    """
    token = os.getenv("TRAE_API_TOKEN")
    if not token:
        # 500 because this is a server misconfiguration, not a client error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfigured: TRAE_API_TOKEN not set",
        )
    return token

async def verify_request(
    user_agent: str | None = Header(default=None, alias="User-Agent"),
    token: str = Depends(get_configured_token),
):
    if not user_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing User-Agent header",
        )
    
    # Token is now securely loaded from environment
    # Additional validation logic can be added here
    return {"user_agent": user_agent, "token_configured": True}