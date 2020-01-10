## Background

## Pipeline
1. Scrape as many coffee shops in California
2. Create json object for each store and input the document to MongoDB
3. Load MongoDB collections to Pandas
4. Clean nested dictionaries and structure df so that each column is a feature

## EDA
I want to explore what are the most important features that Yelp users care about when visiting a coffee shop. We first have to decide a way to measure Yelp users' satisfaction levels. The two values I chose to watch was the star rating ( 0 to 5, in 0.5 intervals) and the number of reviews. The star ratings will provide the obvious insight into how satisfied the customers are. On the other hand, the number of reviews does not directly imply satisfaction but rather engagement, whether it be to complain or praise. 

Looking at the distribution of star ratings, the shape looks close to normal with a skew. 

>>>place graph of rating distribution, reviews, describe()

I got better sense of how our ratings and review_counts are distributed, I wanted to compare the same plot but accross all the different amenities. For each amenity, I looked for shifts in the mean for when the amenity is provided and when it is not. 

>>graph of one amenity and shift in mean

In this situation, a visual representation of counts of simple discrete values can be best shown using a histrogram. However, because the data is descrete and simple an actual number respresentation of the difference along with the graph, provides faster insight.

>>graph of amenities with means as legend

Negative shifts in rating when an amenity exists, provides interesting insights that may not have been considered. For instance, when delivery is available, the average rating will drop by 0.1. This could be due to a lack of better in-store service and less-than optimal staffing. Another interesting one is the "good for children" amenity. Coffee shops that are considered good for children will most likely be louder than average and may not be appealing to many customers who visit coffee shops to study or chat. This pattern is also evident with the "Noise level" amenity. The difference in mean for "Loud" and "Quiet" is highest at 0.31. Lastly, the second largest negative shift was "Accepts Credit Cards." This pattern is not as obvious and harder to explain what is happening. Perhaps a lot of the "hole in the wall" stores usually have more word-of-mouth marketing and generally loved by the community.

Of the amenities that resulted in a positive shift, "Outdoor Seating" and "Catering" were more effective. 



