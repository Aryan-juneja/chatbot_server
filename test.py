import requests
import re

# url = "https://python-backend-alpha.vercel.app/chat"
url = "http://127.0.0.1:5000/chat"
# url="https://python-backend-alpha.vercel.app/chat"
# url="https://pecchat-b.vercel.app/chat"

data = {
    "chat_history": [
        {"role": "user", "content": " hello my name is aryan and my mobile no is 1596324785.suggest me some properties in Brentwood i want a residential house and no price limit with 3 bedroom"},
        {"role": "assistant", "content": "Sure! The 2024 real estate market is expected to be shaped by several factors..."}
    ],
    "buffer_memory": [
        "Interest rates are expected to remain stable in 2024, favoring buyers."
    ]
}
response = requests.post(url, json=data)
response = response.json()
response = response["bot_reply"]
print(response)

# Remove unwanted characters like **, ###, and other symbols
# response = re.sub(r'[\*\#\-\_\=\+\%\^\&\(\)\'\"]', '', response)  # Removes all markdown-like characters

# # Check if the response length is greater than 500
# if len(response) > 500:
#     # Split sections of the response
#     intro_section = response.split("\n\n")[0]
#     properties_section = response.split("\n\n")[1:-1]
#     call_to_action_section = response.split("\n\n")[-1]
    
#     formatted_properties = []
    
#     for property_info in properties_section:
#         # Split property details into lines for better presentation
#         property_details = property_info.strip().split("\n")
        
#         try:
#             # Clean up property name
#             property_name = property_details[0].strip()
        
#             # Ensure there are enough details to process
#             if len(property_details) >= 3:
#                 builder_name = property_details[1].split(":")[1].strip()
#                 specifications = "\n".join(property_details[2:-3]).strip()

#                 # Ensure there are enough elements for project highlights and reasons
#                 if len(property_details) >= 5:
#                     project_highlights = property_details[-3].strip()
#                     why_this_property = property_details[-2].split(":")[1].strip()

#                     # Formatting the property info without using symbols
#                     formatted_properties.append(f"""
#                     {property_name}
#                     Builder: {builder_name}
#                     {specifications}
#                     Project Highlights: {project_highlights}
#                     Why This Property: {why_this_property}
#                     """)
#                 else:
#                     # Handle incomplete property details
#                     formatted_properties.append(f"""
#                     {property_name}
#                     [Information Incomplete]
#                     """)
#             else:
#                 # Handle missing details
#                 formatted_properties.append(f"""
#                 {property_name}
#                 [Property details are incomplete]
#                 """)
#         except Exception as e:
#             # If there's an error, display raw property info
#             formatted_properties.append(f"""
#             Error with Property: {property_info}
#             Error details: {str(e)}
#             """)

#     # Combine the sections to form the final message
#     final_message = f"""
# {intro_section}

# Here are some properties that might interest you:

# {''.join(formatted_properties)}

# {call_to_action_section}
# """
#     # Output the final formatted message
#     print(final_message)
# else:
#     # If the response is short, just print it as is
# print(response)