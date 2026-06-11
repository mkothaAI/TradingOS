Module: Module 10_Trading Systems

Source files used:
- source/Varsity/10 Trading Systems/Module 10_Trading Systems.pdf

Extraction status:
- status: verified (text extracted)
- extraction_date: 2026-05-16T03:20:39.162563Z
- extractor: pdfplumber (text-only extraction)

## Module summary
Table of Contents 1 What to expect? 1 2 Pair Trading logic 6 Pair Trading, Method 1, Chapter 1 (PTM1, C1) -Tracking 3 13 Pairs 4 PTM1, C2 – Pair stats 21 5 PTM1, C3 – Pre trade setup 30 6 PTM1, C4 – The Density Curve 39 7 PTM1, C5 – The Pair Trade 48 Pair trade Method 2, Chapter 1 (PTM2, C1) – Straight line 8 59 Equation 9 PTM2, C2 – Linear Regression 66 10 PTM2, C3 – The Error Ratio 77 11 PTM2, C4 – The ADF test 86 12 Trade Identification 98 13 Live Example – 1 104 14 Live Example – 2 117 15 Calendar Spreads 121 16 Momentum Portfolios 130

## Chapter-by-chapter notes
- Detected chapter marker on page 2: Table of Contents 1 What to expect? 1 2 Pair Trading logic 6 Pair Trading, Method 1, Chapter 1 (PTM1, C1) -Tracking 3 13 Pairs 4 PTM1, C2 – Pair stats 21 5 PTM1, C3 – Pre trade setup 30 6 PTM1, C4 – The Density Curve 39 7 PTM1, C5 – The Pai
- Detected chapter marker on page 3: CHAPTER 1 What to expect? 1.1 – What is a trading system? Such a glorious day to start this module! Here is the headline that rocked the stock markets today – Yesterday i.e. 24th Oct 2017, the Finance Minister announced that the Government 
- Detected chapter marker on page 8: CHAPTER 2 Pair Trading logic 2.1 – The idea If you have ever been on an interstate highway, then you would have noticed that the highway usually includes the main highway, on which the vehicles zoom by at full speed. On either side of the h
- Detected chapter marker on page 13: To be market neutral, you need to be – long and short, on the same underlying, at the same time. A good example here is the calendar spread. In a calendar spread, you are long and short on the same underlying expiring on two different dates
- Detected chapter marker on page 15: CHAPTER 3 Pair Trading, Method 1, Chapter 1 (PTM1, C1) -Tracking Pairs 3.1 – Getting you familiar with Jargons Like I had mentioned in the previous chapter, there are two techniques based on which you can pair trade. The first technique tha
- Detected chapter marker on page 22: While we are at it, one more point on correlation. This bit is only for those interested in the math part of correlation. The correlation data makes sense only if the data series is ‘stationary around the mean’. What does this mean? – Well,
- Detected chapter marker on page 23: CHAPTER 4 PTM1, C2 – Pair stats 4.1 – Correlation and its types I have to mention this at this point. The pair trading technique we are discussing now is discussed in a book called, ‘Trading Pairs’, by Mark Whistler. I like this book for th
- Detected chapter marker on page 30: 23, 34, 44, 51, 55, 65, 72, 82, 100, 100 Since there are even numbers of observation, I’ll take the middle two numbers i.e. 55 and 65, their average represents the median. Median = (55 + 65)/2 =60 The excel function to calculate median is ‘
- Detected chapter marker on page 32: CHAPTER 5 PTM1, C3 – Pre trade setup 5.1 – Revisiting the Normal Distribution If you have been a regular reader on Varsity, then chances are you’d have come across the discussion on Normal Distribution in the Options Module. If you’re not, 
- Detected chapter marker on page 34: The Excel functions are as follows – 1. Mean – ‘=average()’ 2. Median – ‘=median()’ 3. Mode – ‘=mode.mult()’ And the numbers are as below – As you may notice, the correlation numbers were calculated in the previous chapter. We now have the 
- Detected chapter marker on page 40: So if the 498th differential data read 315, then we can quickly understand that the value is around the +2 standard deviations and with 95% confidence you could conclude that there is only 5% chance for the next set of data points to go hig
- Detected chapter marker on page 41: CHAPTER 6 PTM1, C4 – The Density Curve 6.1 – A quick recap I think a quick recap is justified at this stage, this is to ensure we are all on the same page. I’d strongly recommend you read through the recap, to ensure we are on track. I’ll k
- Detected chapter marker on page 48: You can use the inbuilt excel function called Norm.dist for this. The function requires 4 inputs – o X – this is the daily ratio value o Mean – this is the mean or average value of the ratio o Standard Deviation – this is the standard devia
- Detected chapter marker on page 50: CHAPTER 7 PTM1, C5 – The Pair Trade 7.1 – Quick Reminder We closed the previous chapter with a note on Density curve and how the value of the density curve helps us spot pair trading opportunity. In this chapter, we will work towards identi
- Detected chapter marker on page 59: I hope the P&L of pair trade is incentivizing you enough to learn more about pair trading. I’ll deliberately stop here, to ensure you soak in everything that we have discussed. I’ll leave you with few final points. 1. Everything we have lea
- Detected chapter marker on page 61: CHAPTER 8 Pair trade Method 2, Chapter 1 (PTM2, C1) – Straight line Equation 8.1 – A straight relationship Today happens to be 14th of Feb, people around me are excited about Valentine’s Day, they are busy celebrating love and relationships
- Detected chapter marker on page 67: X is the independent variable and Y is the dependent variable. Given this, do you see a relationship between these two sets of numbers here? Eyeballing the numbers suggest that there is no relationship between X and Y, definitely not like t
- Detected chapter marker on page 68: CHAPTER 9 PTM2, C2 – Linear Regression 9.1 – Introduction to Linear Regression The previous chapter laid down a basic understanding of a straight line equation. To keep things simple, we took a very basic example to explain how two variable
- Detected chapter marker on page 78: I’ve also highlighted the residual when x = 18, which is what we calculated above. To give you a heads up – the bulk of the focus for carrying out the relative value trade depends on the residuals. Stay tuned! Download the excel sheet here.
- Detected chapter marker on page 79: CHAPTER 10 PTM2, C3 – The Error Ratio 10.1 – Who is X and who is Y? I hope the previous chapter gave you a basic understanding of linear regression and how one can conduct the linear regression operation on two sets of data, on MS Excel. Re
- Detected chapter marker on page 87: Anyway, the error ratio, as we know – Error Ratio = Standard Error of Intercept / Standard Error I’m calculated the same for – 1. ICICI as X and HDFC as y = 0.401 2. HDFC as X and ICICI as y = 0.227 The decision to designate X and Y to stoc
- Detected chapter marker on page 88: CHAPTER 11 PTM2, C4 – The ADF test 11.1 – Co-Integration of two-time series I guess this chapter will get a little complex. We would be skimming the surface of some higher order statistical theory. I will try my best and stick to practical 
- Detected chapter marker on page 98: In fact, if you look at the snapshot above, you will find only 2 pairs which have the desired p-value i.e. Kotak and PNB with a P value of 0.01 and HDFC and PNB with a P value of 0.037. The p values don’t usually change overnight. Hence, fo
- Detected chapter marker on page 100: CHAPTER 12 Trade Identification 12.1 – Trading the equation At this stage, we have discussed pretty much all the background information we need to know about Pair trading. We now have to patch things together and understand how all these co
- Detected chapter marker on page 103: So here is the equation again – y = M*x + c + ε If this equation were to be true, then by going long and short on y and x, we are hedging away the directional risk associated with this pair. This leaves us with the 2nd part of the equation 
- Detected chapter marker on page 104: Like in the first method, the idea here is to initiate a trade at the 2nd standard deviation and hold the trade till the residual reverts to mean. The SL can be kept at 3SD for both the trades. More on this in the next chapter. I know this 
- Detected chapter marker on page 106: CHAPTER 13 Live Example -1 13.1 – Tracking the pair data We have finally reached a point where we are through with all the background theory knowledge required for Pair Trading. I know most of you have been waiting for this moment In this l
- Detected chapter marker on page 108: know where it lies and plan your trades. Of course, we will discuss more on this later in this chapter. 13.2 – Note for the programmers In Chapter 11, I introduced the ‘Pair Data’ sheet. This sheet is an output of the Pair Trading Algo. The
- Detected chapter marker on page 118: Beyond Pair, trading lies something called as multivariate regression. By no stretch of the imagination is this easy to understand, but let me tell you if you can graduate to this arena, the game is different. Download the Position Tracker 
- Detected chapter marker on page 119: CHAPTER 14 Live Example – 2 14.1 – Position Sizing I know, the discussion on pair trading was to end with the previous chapter, but I thought I had to discuss a special case before we finally wrap up. I’ll also try and keep this chapter rea
- Detected chapter marker on page 123: CHAPTER 15 Calendar Spreads 15.1 – The classic approach I had briefly introduced the concept of calendar spreads in Chapter 10 of the Futures Trading module. Traditionally calendar spreads are dealt with a price based approach. Here is a qu
- Detected chapter marker on page 125: Calculate the daily historic difference between the two contracts and generate a time series. Calculate the mean and standard deviation of the time series. Using the mean and standard deviation data we can estimate the range for the differe
- Detected chapter marker on page 132: CHAPTER 16 Momentum Portfolios 16.1 – Defining Momentum If you have spent some time in the market, then I’m quite certain that you’ve been bombarded with market jargons of all sorts. Most of us get used to these jargons and in fact, start u
- Detected chapter marker on page 135: Stock A, has trended up consistently on a day to day basis, while stock B has been quite a dud all along except for the last two days. On an overall basis if you check the percentage change over the 7-day period then both have delivered sim
- Detected chapter marker on page 145: 16.5 – Word of caution As good as it may seem, the price based momentum strategy works well only when the market is trending up. When the markets turn choppy, the momentum strategy performs poorly, and when the markets go down, the momentum

## Open questions / missing material
- PDF references images or Excel screenshots; images were detected but not captured as structured data. Consider supplying original workbooks or higher-resolution images for precise reproduction.

## Notes on extraction quality
- Generated from text-only extraction; tables and images may be incomplete.
