import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import re


def clean_text(text):
    # Remove HTML tags
    text = re.sub("<[^<]+?>", "", text) if text else ""
    # Remove leading/trailing whitespaces
    text = text.strip()
    # Replace consecutive whitespaces with a single space
    text = re.sub(r"\s+", " ", text)
    return text


# Streamlit app configuration
st.title("XML to CSV Converter")
st.write("Upload your XML file and convert it to CSV.")

uploaded_file = st.file_uploader("Choose an XML file", type="xml")

if uploaded_file is not None:
    # Parse the XML file
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    # Initialize lists for storing question data
    single_choice_questions = []
    multiple_choice_questions = []

    # Iterate through each item in the XML
    for item in root.findall("item"):
        ident = item.get("ident")
        title = item.get("title")
        question_text = clean_text(item.find(".//material/mattext").text)

        responses = []
        response_labels = {}
        for response_label in item.findall(".//response_label"):
            response_id = response_label.get("ident")
            response_text = clean_text(response_label.find("material/mattext").text)
            responses.append((response_id, response_text))
            response_labels[response_id] = response_text

        correct_responses = set()
        incorrect_responses = set()
        for respcondition in item.findall(".//respcondition"):
            displayfeedback = respcondition.find(".//displayfeedback")
            if (
                displayfeedback is not None
                and displayfeedback.get("linkrefid") == "response_allcorrect"
            ):
                conditionvar = respcondition.find(".//conditionvar")
                if conditionvar is not None:
                    # Direct varequal elements inside conditionvar
                    for varequal in conditionvar.findall("./varequal"):
                        correct_responses.add(varequal.text)
                    # Exclude varequal elements inside 'not' elements
                    for not_element in conditionvar.findall("./not"):
                        for varequal in not_element.findall("./varequal"):
                            incorrect_responses.add(varequal.text)
                            print(incorrect_responses)

        correct_answers = [
            response_labels[response_id] for response_id in correct_responses
        ]
        incorrect_answers = [
            response_labels[response_id] for response_id in incorrect_responses
        ]

        # Extract correct and incorrect feedback
        correct_feedback = ""
        incorrect_feedback = ""
        feedback_elements = item.findall(".//itemfeedback")
        for feedback_element in feedback_elements:
            feedback_ident = feedback_element.get("ident")
            feedback_text = (
                clean_text(feedback_element.find(".//flow_mat/material/mattext").text)
                if feedback_element.find(".//flow_mat/material/mattext") is not None
                else ""
            )
            if feedback_text:
                if feedback_ident == "response_allcorrect":
                    correct_feedback = feedback_text
                elif feedback_ident == "response_onenotcorrect":
                    incorrect_feedback = feedback_text

        question_data = {
            "ident": ident,
            "title": title,
            "question_text": question_text,
            "correct_answers": ", ".join(correct_answers),
            "incorrect_answers": ", ".join(incorrect_answers),
            "correct_feedback": correct_feedback,
            "incorrect_feedback": incorrect_feedback,
        }

        question_type = None
        for metadata in item.findall(".//qtimetadatafield"):
            if metadata.find("fieldlabel").text == "QUESTIONTYPE":
                question_type = metadata.find("fieldentry").text
                break

        if question_type == "SINGLE CHOICE QUESTION":
            single_choice_questions.append(question_data)
        elif question_type == "MULTIPLE CHOICE QUESTION":
            multiple_choice_questions.append(question_data)

    # Create DataFrames from the question lists
    single_choice_df = pd.DataFrame(single_choice_questions)
    multiple_choice_df = pd.DataFrame(multiple_choice_questions)

    # Save DataFrames to CSV
    single_choice_csv = single_choice_df.to_csv(index=False).encode("utf-8")
    multiple_choice_csv = multiple_choice_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Single Choice Questions CSV",
        data=single_choice_csv,
        file_name="single_choice_questions.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download Multiple Choice Questions CSV",
        data=multiple_choice_csv,
        file_name="multiple_choice_questions.csv",
        mime="text/csv",
    )

    st.success("CSV files have been generated and are ready for download.")
