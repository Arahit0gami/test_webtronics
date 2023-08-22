_not_found_post = {
    "title": "Not found post",
    "description": "Post with id={post_id} not found",
    "example": {
        "description": "Post with id={post_id} not found"
    }
}

swagger_like_post = {
    "responses": {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "oneOf": [
                            {
                                "type": "string",
                                "enum": [
                                    "The reaction is like delivered",
                                    "Reaction removed",
                                    "The reaction is dislike delivered",
                                    "The reaction has not been changed",
                                ]
                            },
                        ]
                    }
                }
            },
            "required": True,
        },
        "404": {
            "description": "Not found post",
            "content": {
                "application/json": {
                    "schema": _not_found_post,
                }
            },
        }
    },
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "anyOf": [
                        {
                            "required": [
                                "like",
                            ],
                            "description": "like: 'on' or 'off'",
                            "example": {"like": "on"},
                            "title": "like"
                        },
                        {
                            "required": [
                                "dislike",
                            ],
                            "description": "dislike: 'on' or 'off'",
                            "example": {"dislike": "off"},
                            "title": "dislike"
                        }
                    ],
                }
            }
        }
    },
}

swagger_get_post = {
    "404": {
        "description": "Bad request",
        "content": {
            "application/json": {
                "schema": _not_found_post,
            }
        },
    },
}

swagger_update_post = {
    **swagger_get_post,
    "403": {
        "description": "Bad request",
        "content": {
            "application/json": {
                "schema": {
                    "title": "Right to edit",
                    "description": "You can't edit a "
                                   "post with id={post_id}",
                    "example": {
                        "description": "You can't edit a "
                                       "post with id={post_id}"
                    },
                },
            }
        }
    },
}

swagger_delete_post = {
    **swagger_update_post,
    "200": {
        "content": {
            "application/json": {
                "schema": {
                    "title": "Successful Response",
                    "description": "Post with id={post_id} successfully deleted",
                    "example": "Post with id={post_id} successfully deleted"
                }
            }
        },
        "required": True,
    },
}
