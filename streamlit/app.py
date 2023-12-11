import streamlit as st
from auth_user import create_user,login_user
# from utils import get_diet_answers
import sys
sys.path.insert(0, '../serpapi_data_ingestion')
sys.path.insert(1, '../snowflake')
from main import get_map #get_reviews
from eda import eda
from snowflake_data import *
import plotly.express as px
from bardapi import BardCookies


load_dotenv('/Users/harsh/GenAI/Bitebuddy/BiteBuddy/.env')
# Access variables
token1 = os.getenv("ID")
token2 = os.getenv("IDTS")
token3 = os.getenv("IDCC")

cookie_dict = {
    "__Secure-1PSID": token1,
    "__Secure-1PSIDTS": token2,
    "__Secure-1PSIDCC": token3,
}

bard = BardCookies(cookie_dict=cookie_dict)

#dummy comment


st.set_page_config(page_title="BiteBuddy", layout="wide")
with st.sidebar:
    # options menu
    selected = st.selectbox("Menu", ["Log In", 'Sign Up'])
    
    # log in form
    if 'login' not in st.session_state:
        st.session_state['login'] = False



    if selected == "Log In":
        
        st.write('## Log In')
        login_username = st.text_input('Email')
        login_password = st.text_input('Password', type='password')
        # authentication status update
        if st.button('Log In!'):
            # send login request
            st.session_state['login'] = login_user(login_username,login_password)

        if st.session_state['login'] == True:
            if st.button("Logout"):
                st.session_state['login'] = False

    # # Sign-up form
    if selected == "Sign Up":
        st.write('## Sign up')
        name = st.text_input('Name')
        username = st.text_input('Email',key='signup_username')
        password = st.text_input('Password', type='password',key='signup_pass')
        confirm_password = st.text_input('Confirm Password', type='password')

        
        if st.button('Sign up'):
            if password != confirm_password:
                st.write("Passwords don't Match!")
            else:
                # send register request
                signup_status = create_user(name,username,password)
                if signup_status:
                    st.success("User Registered Successfully! Sign-in to continue...")
                else:
                    st.error("Email already exists! Sign in to continue...")

if  st.session_state['login'] != True:
    st.title("Still Staring at the restuarant menu??😶")
    st.image('images/3.webp', width=550)
    st.title("Let us help... will you?")
    
if  st.session_state['login'] == True:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", "Explore a Restaurant🔎" ,"Feedback📝", "Bitebuddy Documentation📃", "Monitoring📊"])
    with tab1:
        st.title("Welcome to your.... BITEBUDDY! 🍽️")

        eda()
    with tab2:
        st.header("Pick a restaurant!")

        #select box for restaurant names
        restaurant_list = get_restaurants()
        selected_restaurant = st.selectbox("Select a restaurant:", restaurant_list)
        # Fixing restaurant name for SQL query
        selected_restaurant = selected_restaurant.replace("'", "''")
        # testing
        # print(f"SELECT business_name, review_text FROM DAMG7374.staging.sample_reviews WHERE BUSINESS_NAME = '{selected_restaurant}' LIMIT 10")

        if st.button("Get Dish Recommendations"):

            st.toast('Warming up BiteBuddy...')
            snowflake_df = get_reviews_summary(selected_restaurant)
            snowflake_df = recommendation_score(snowflake_df)
            # Testing
            # st.write(snowflake_df)

            # DATAFRAME CLEANING:
            # snowflake_df.rename(columns={'CLUSTER_LABEL': 'MEAL_NAME'}, inplace=True)
            snowflake_df = snowflake_df[['BUSINESS_NAME', 'MEAL_NAME', 'RECOMMENDATION_SCORE', 'TOTAL_REVIEWS', 'AVG_REVIEW_RATING', 'AVG_MEAL_SENTIMENT']].sort_values(by='RECOMMENDATION_SCORE', ascending=False)
            # List of keywords to filter out
            keywords_to_filter = ['food', 'drink', 'restaurant', '', 'price', 'breakfast', 'brunch', 'lunch', 'dinner', 'delicious', 'tasty', 'service', 'atmosphere']

            # Drop rows where 'MEAL_NAME' contains any of the specified keywords and 'TOTAL_REVIEWS' is less than 2 and 'MEAL_NAME' contains 'food'
            snowflake_df = snowflake_df[(~snowflake_df['MEAL_NAME'].str.lower().isin(keywords_to_filter)) & 
                                        (snowflake_df['TOTAL_REVIEWS'] >= 2) & 
                                        (~snowflake_df['MEAL_NAME'].str.contains('food', case=False))]


            st.header("Hmm, here's what people say.....")
            st.subheader("10 Most Recent Reviews:")
            df, formatted_reviews = get_reviews(selected_restaurant)
            # st.write(df)
            st.text_area(label="",value=formatted_reviews, height=200)
   
            st.write("---")
            st.header("Well, here's what BITEBUDDY says.....")
            # Display the DataFrame without the index
            st.dataframe(snowflake_df, hide_index=True)
            st.divider()

            #####################################################
            # RLHF:
            #####################################################


            #####################################################
            # Dietary Restrictions:
            #####################################################
            st.info('Model: The AI model isn''t perfect, so make sure to double check the dietary restrictions output before consuming the meal!', icon="⚠️")
            questions = [
                "Does this dish contain gluten?",
                "Are there nuts in this meal?",
                "Is this dish suitable for vegetarians?",
                "Is this dish spicy?",
                # Add more questions here...
            ]
            meal_names = snowflake_df[['MEAL_NAME']]
            # Streamlit app
            st.subheader("Ask Dietary Questions about Meals")


            selected_meal = None
            selected_question = None

            if selected_meal is None:
                selected_meal = st.selectbox("Select your recommended meal", meal_names)

            if selected_question is None:
                selected_question = st.selectbox("Select a dietary question", questions)

            # Check if both selections have been made
            if selected_meal and selected_question:
                input_prompt = "I am eating {}. {}".format(selected_meal, selected_question)
                print("2:", input_prompt)
                bard_result = bard.get_answer(input_prompt)['content']
                print(bard_result)
                st.write(bard_result)
                    # st.experimental_rerun()


            # user_input = st.text_input("Ask a question to our AI bot!")

            # if st.button("Get Answer!"):
            #     # Check if user input exists and is not empty
            #     if user_input:
            #         print(user_input)
            #         user_bard_result = bard.get_answer(user_input)['content']
            #         if user_bard_result:
            #             print(user_bard_result)
            #             st.write(user_bard_result)


    with tab3:
            st.header("Help us help you. We value your Feedback!")

            #select box for restaurant names
            restaurant_list = get_restaurants()
            selected_restaurant = st.selectbox("Select a restaurant to provide feedback:", restaurant_list)
            # Fixing restaurant name for SQL query
            selected_restaurant = selected_restaurant.replace("'", "''")

            snowflake_df = get_reviews_summary(selected_restaurant)
            meal_names = snowflake_df[['MEAL_NAME']]
            selected_meal = st.selectbox("Select the meal you were recommended:", meal_names)
            

            positive_feedback = None

            if selected_meal:
                col1, col2 = st.columns(2)

                if col1.button("Yay! I liked the Bitebuddy meal recommendation"):
                    positive_feedback = 1  # Set positive feedback value to 1

                if col2.button("Nay! I disliked the Bitebuddy meal recommendation"):
                    positive_feedback = 0  # Set positive feedback value to 0 if negative

                if positive_feedback is not None:
                    st.success(f"Feedback stored: {'Positive' if positive_feedback else 'Negative'}")
                    # You can store the feedback value here in a database or use it as needed




    with tab4:
        st.title("Documentation... Coming Soon!")
        st.write("Check out our GitHub Repo for more details! Lets put details about the LLM and project here!")
        # dummy comment


    with tab5:
        # Only have access to this tab if logged in as admin else redirect to home page
        st.title("Monitoring... Coming Soon!")
        st.write("Admin Monitoring Reports will be displayed here!")

        #####################################################
        # Feedback Monitoring:
        #####################################################
        df = get_feedback_summary()
        st.subheader("Feedback Details:")
        st.write(df)

        st.title("Feedback Over Time")

        # Bar chart
        st.bar_chart(df.set_index('CREATE_DATE')[['TOTAL_POS_FEEDBACK', 'TOTAL_NEG_FEEDBACK']])

        st.subheader("Feedback Summary:")
        # st.write(df.columns)
        # List of columns for which you want to calculate the sum
        columns_to_sum = ["TOTAL_RESTAURANTS_FEEDBACK", "TOTAL_MEALS_FEEDBACK", "TOTAL_FEEDBACK", "TOTAL_POS_FEEDBACK", "TOTAL_NEG_FEEDBACK"]

        # Calculate the sum of selected columns and create a new row in the DataFrame
        sum_row = df[columns_to_sum].sum().to_frame().T
        sum_row['POSITIVE_FEEDBACK_PERC'] = round(sum_row['TOTAL_POS_FEEDBACK'] / sum_row['TOTAL_FEEDBACK'] * 100, 1)
        st.write(sum_row)
        # st.write(sum_df)
        st.divider()


        #####################################################
        # Snowflake Usage Monitoring:
        #####################################################
        st.subheader("Snowflake Usage Overview:")
        st.info("For more details see the Streamlit app in Snowflake - https://app.snowflake.com/pjpbfql/knb43715/#/streamlit-apps/DAMG7374.PUBLIC.NENLD3FVOT0GSA9I?ref=snowsight_shared!", icon="ℹ️")
        st.divider()

        #############################################
        #     Credit Usage Total (Bar Chart)
        #############################################
        #Credits Usage (Total)
        total_credits_used_df = get_credit_usage()

        #Chart
        fig_credits_used=px.bar(total_credits_used_df,x='TOTAL_CREDITS_USED',y='WAREHOUSE_NAME',orientation='h',title="Credits Used by Warehouse")
        fig_credits_used.update_traces(marker_color='green')
        st.plotly_chart(fig_credits_used)

        #############################################
        #     Credits Billed by Month
        #############################################
        credits_billed_df = get_credit_usage_month()
        #st.write(credits_billed_df)
        fig_credits_billed=px.bar(credits_billed_df,x='USAGE_MONTH',y='SUM(CREDITS_BILLED)', orientation='v',title="Credits Billed by Month")
        st.plotly_chart(fig_credits_billed, use_container_width=True)

        #############################################
        #     Credits Used Overtime
        #############################################
        #Credits Used Overtime
        credits_used_overtime_df = get_credit_usage_over_time()
        #chart
        fig_credits_used_overtime_df=px.bar(credits_used_overtime_df,x='USAGE_DATE',y='TOTAL_CREDITS_USED',color='WAREHOUSE_NAME',orientation='v',title="Credits Used Overtime")
        st.plotly_chart(fig_credits_used_overtime_df, use_container_width=True)
