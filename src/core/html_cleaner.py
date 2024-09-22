from bs4 import BeautifulSoup
from copy import deepcopy


def clean_body_html(html_content):
    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the <body> tag
    body = soup.find("body")

    if body:
        # Remove <style> tags within the body
        for style in body.find_all("style"):
            style.decompose()

        for br in body.find_all("br"):
            br.decompose()

        # Remove specific unwanted attributes
        attribute_to_remove = [
            "border",
            "cellpadding",
            "cellspacing",
            "bgcolor",
            "height",
            "width",
            "align",
            "valign",
            "halign",
            "leftmargin",
            "marginheight",
            "marginwidth",
            "offset",
            "style",
            "topmargin",
            "alt",
        ]
        for tag in soup.find_all(True):  # True finds all tags
            # Remove specific unwanted attributes
            for attribute in attribute_to_remove:
                if attribute in tag.attrs:
                    # if attr in attribute_to_remove:
                    del tag[attribute]

        # Return cleaned HTML within the body
        return str(body)
    return ""


def minify_html(html_content, domain, attributes=["href", "src"], tags_to_remove=["img"]):
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove specified tags
    for tag in tags_to_remove:
        for match in soup.find_all(tag):
            match.decompose()

    # Find all tags with specified attributes and keep only those attributes
    selected_tags = []
    for tag in soup.find_all():
        if tag and any(tag.has_attr(attr) for attr in attributes):
            filtered_tag = deepcopy(tag)  # Create a copy of the tag
            # Keep only specified attributes that contain the domain
            filtered_tag.attrs = {
                attr: filtered_tag.attrs[attr]
                for attr in attributes
                if attr in filtered_tag.attrs and domain in filtered_tag.attrs[attr]
            }
            if filtered_tag.attrs:  # Only add if there are any attributes left
                selected_tags.append(str(list(filtered_tag.attrs.values())[0]))  # Convert to string

    return "        ".join(selected_tags)  # Join selected tags as a single string
