def analyze_thoughts():
    user_id = ObjectId('6619680beb81d71a1f936c28')

    thoughts = db.thoughts.find({'user_id': '6619680beb81d71a1f936c28'})

    if not thoughts:
        app.logger.error('No thought IDs provided')

    try:
        for thought in thoughts:
            if thought and not thought.get('analysis'):
                # Perform analysis on the thought
                create_analysis(thought['_id'], thought['raw_text'], thought['inspiration_words'])
                app.logger.info(f'Added Analysis to thought {thought["_id"]}')
        app.logger.info('Thoughts analyzed successfully')
    except Exception as e:
        app.logger.error(f"Error analyzing thoughts: {str(e)}", exc_info=True)

analyze_thoughts()