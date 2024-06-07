import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

# Streamlit app configuration
st.title('XML to CSV Converter')
st.write('Upload your XML file and convert it to CSV.')

uploaded_file = st.file_uploader("Choose an XML file", type="xml")

if uploaded_file is not None:
    # Parse the XML file
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    # Initialize lists for storing question data
    single_choice_questions = []
    multiple_choice_questions = []

    # Iterate through each item in the XML
    for item in root.findall('item'):
        ident = item.get('ident')
        title = item.get('title')
        question_text = item.find('.//material/mattext').text
        
        responses = []
        response_labels = {}
        for response_label in item.findall('.//response_label'):
            response_id = response_label.get('ident')
            response_text = response_label.find('material/mattext').text
            responses.append((response_id, response_text))
            response_labels[response_id] = response_text
        
        correct_responses = set()
        for respcondition in item.findall('.//respcondition'):
            displayfeedback = respcondition.find('.//displayfeedback')
            if displayfeedback is not None and displayfeedback.get('linkrefid') == 'response_allcorrect':
                conditionvar = respcondition.find('.//conditionvar')
                if conditionvar is not None:
                    # Direct varequal elements inside conditionvar
                    for varequal in conditionvar.findall('./varequal'):
                        correct_responses.add(varequal.text)
                    # Exclude varequal elements inside 'not' elements
                    for not_element in conditionvar.findall('./not'):
                        for varequal in not_element.findall('./varequal'):
                            correct_responses.discard(varequal.text)
        
        marked_responses = []
        for response_id, response_text in responses:
            if response_id in correct_responses:
                marked_responses.append(f"<CORRECT ANSWER> {response_text}")
            else:
                marked_responses.append(f"<INCORRECT ANSWER> {response_text}")
        
        # Extract feedback
        feedback_elements = item.findall('.//itemfeedback')
        feedbacks = []
        for feedback_element in feedback_elements:
            feedback_text = feedback_element.find('.//flow_mat/material/mattext').text if feedback_element.find('.//flow_mat/material/mattext') is not None else ''
            if feedback_text:  # Ensure feedback text is not None or empty
                feedbacks.append(feedback_text)
        
        feedback = " | ".join(feedbacks) if feedbacks else ''
        
        question_data = {
            'ident': ident,
            'title': title,
            'question_text': question_text,
            'response_0': marked_responses[0] if len(marked_responses) > 0 else '',
            'response_1': marked_responses[1] if len(marked_responses) > 1 else '',
            'response_2': marked_responses[2] if len(marked_responses) > 2 else '',
            'response_3': marked_responses[3] if len(marked_responses) > 3 else '',
            'response_4': marked_responses[4] if len(marked_responses) > 4 else '',
            'response_5': marked_responses[5] if len(marked_responses) > 5 else '',
            'response_6': marked_responses[6] if len(marked_responses) > 6 else '',
            'response_7': marked_responses[7] if len(marked_responses) > 7 else '',
            'response_8': marked_responses[8] if len(marked_responses) > 8 else '',
            'response_9': marked_responses[9] if len(marked_responses) > 9 else '',
            'feedback': feedback
        }

        question_type = None
        for metadata in item.findall('.//qtimetadatafield'):
            if metadata.find('fieldlabel').text == 'QUESTIONTYPE':
                question_type = metadata.find('fieldentry').text
                break

        if question_type == 'SINGLE CHOICE QUESTION':
            single_choice_questions.append(question_data)
        elif question_type == 'MULTIPLE CHOICE QUESTION':
            multiple_choice_questions.append(question_data)

    # Create DataFrames from the question lists
    single_choice_df = pd.DataFrame(single_choice_questions)
    multiple_choice_df = pd.DataFrame(multiple_choice_questions)

    # Save DataFrames to CSV
    single_choice_csv = single_choice_df.to_csv(index=False).encode('utf-8')
    multiple_choice_csv = multiple_choice_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download Single Choice Questions CSV",
        data=single_choice_csv,
        file_name='single_choice_questions.csv',
        mime='text/csv',
    )

    st.download_button(
        label="Download Multiple Choice Questions CSV",
        data=multiple_choice_csv,
        file_name='multiple_choice_questions.csv',
        mime='text/csv',
    )

    st.success('CSV files have been generated and are ready for download.')
