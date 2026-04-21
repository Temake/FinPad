"""Add gamification badges, education tips + update user_stats

Revision ID: 002
Revises: 001
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create financial_tips table
    op.create_table(
        'financial_tips',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('icon', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed default badges
    op.execute("""
        INSERT INTO badges (name, description, icon, criteria_type) VALUES
        ('First Step', 'Logged your first expense', '🎯', 'first_expense'),
        ('Consistent', '3-day logging streak', '⭐', 'streak_3'),
        ('On Fire', '7-day logging streak', '🔥', 'streak_7'),
        ('Two Weeks Strong', '14-day logging streak', '💪', 'streak_14'),
        ('Monthly Champion', '30-day logging streak', '🏆', 'streak_30'),
        ('Unstoppable', '60-day logging streak', '🚀', 'streak_60'),
        ('Legend', '90-day logging streak', '👑', 'streak_90'),
        ('Getting Started', 'Logged 10 expenses', '📝', 'expenses_10'),
        ('Dedicated', 'Logged 50 expenses', '📊', 'expenses_50'),
        ('Centurion', 'Logged 100 expenses', '💯', 'expenses_100'),
        ('Money Master', 'Logged 500 expenses', '💎', 'expenses_500');
    """)

    # Seed financial tips (100+ tips covering all categories)
    op.execute("""
        INSERT INTO financial_tips (title, content, category, icon, is_active) VALUES
        -- Savings Tips (20)
        ('The 50/30/20 Rule', 'Allocate 50% of income to needs, 30% to wants, and 20% to savings. This simple framework helps balance enjoying life while building financial security.', 'savings', '💰', true),
        ('Pay Yourself First', 'Set up automatic transfers to savings as soon as you receive your salary. Treat savings as a non-negotiable expense.', 'savings', '🏦', true),
        ('Emergency Fund Goal', 'Aim to save 3-6 months of expenses as an emergency fund. Start with ₦50,000 and build up gradually.', 'savings', '🛡️', true),
        ('The Naira Jar Method', 'Keep separate jars (or accounts) for different goals: bills, savings, fun money. Visual separation helps control spending.', 'savings', '🏺', true),
        ('Round Up Savings', 'Round up every purchase to the nearest ₦100 and save the difference. ₦2,350 becomes ₦2,400, saving ₦50.', 'savings', '🔄', true),
        ('The 24-Hour Rule', 'Wait 24 hours before making any non-essential purchase over ₦5,000. Many impulse buys disappear overnight.', 'savings', '⏰', true),
        ('Savings Challenge', 'Try the 52-week challenge: Save ₦100 week 1, ₦200 week 2, etc. By year end, you will have saved ₦137,800!', 'savings', '📅', true),
        ('Automate Everything', 'Set standing orders for savings on payday. What you do not see, you do not spend.', 'savings', '🤖', true),
        ('Small Wins Matter', 'Even saving ₦500 daily adds up to ₦182,500 per year. Small consistent actions build wealth.', 'savings', '🎯', true),
        ('Savings Account Interest', 'Keep your emergency fund in a high-yield savings account. Some Nigerian banks offer up to 4% interest.', 'savings', '📈', true),
        ('The Envelope System', 'Withdraw cash and divide into envelopes for categories. When an envelope is empty, stop spending in that category.', 'savings', '✉️', true),
        ('No-Spend Days', 'Challenge yourself to 2-3 no-spend days per week. Cook at home and find free entertainment.', 'savings', '🚫', true),
        ('Save Your Raises', 'When you get a salary increase, save at least half of it before lifestyle inflation kicks in.', 'savings', '📊', true),
        ('Visual Goals', 'Put a picture of your savings goal (car, house, vacation) on your phone wallpaper for daily motivation.', 'savings', '🖼️', true),
        ('Track Net Worth', 'Calculate your net worth monthly (assets minus debts). Watching it grow is powerful motivation.', 'savings', '📉', true),
        ('The Latte Factor', 'Small daily expenses add up. A ₦1,000 daily coffee is ₦365,000 yearly. Make some at home!', 'savings', '☕', true),
        ('Money Date', 'Schedule a weekly 30-minute money date to review spending and set goals. Consistency builds awareness.', 'savings', '📆', true),
        ('Sinking Funds', 'Save monthly for predictable expenses like car maintenance, birthdays, or December holidays.', 'savings', '🎁', true),
        ('Cash Buffer', 'Keep a small buffer (₦20,000-50,000) in your checking account to avoid overdrafts and stress.', 'savings', '🔒', true),
        ('Celebrate Progress', 'When you hit a savings milestone, celebrate with something small and meaningful. Progress deserves recognition!', 'savings', '🎉', true),

        -- Budgeting Tips (20)
        ('Know Your Numbers', 'Track every expense for one month to understand where your money actually goes. Awareness is the first step.', 'budgeting', '📊', true),
        ('Zero-Based Budget', 'Give every naira a job. Income minus expenses should equal zero, with savings being an expense.', 'budgeting', '🎯', true),
        ('Needs vs Wants', 'Before any purchase, ask: Is this a need or a want? Needs come first, wants fit what is left.', 'budgeting', '🤔', true),
        ('Budget Categories', 'Group expenses: Housing, Transport, Food, Utilities, Savings, and Fun. Allocate percentages to each.', 'budgeting', '📁', true),
        ('Fixed vs Variable', 'Identify fixed costs (rent, subscriptions) vs variable (food, entertainment). Fixed are easier to optimize.', 'budgeting', '📋', true),
        ('Weekly Check-ins', 'Review your budget weekly, not just monthly. Catching issues early prevents month-end surprises.', 'budgeting', '📅', true),
        ('Budget Buffer', 'Add a 10% buffer to your budget for unexpected small expenses. Life rarely goes exactly as planned.', 'budgeting', '🛡️', true),
        ('Category Flexibility', 'If you underspend in one category, move the extra to another or savings. Stay flexible within limits.', 'budgeting', '🔄', true),
        ('Annual Expenses', 'Divide yearly expenses (insurance, subscriptions) by 12 and save monthly. No more surprise big bills!', 'budgeting', '📆', true),
        ('The Fun Budget', 'Always include a fun/entertainment budget. Total restriction leads to burnout and budget abandonment.', 'budgeting', '🎮', true),
        ('Subscription Audit', 'Review all subscriptions quarterly. Cancel what you do not use. Average person wastes ₦15,000/month on unused subs.', 'budgeting', '🔍', true),
        ('Meal Planning', 'Plan meals weekly before shopping. This reduces food waste and prevents expensive last-minute takeout.', 'budgeting', '🍽️', true),
        ('Cash Envelope Variant', 'Use a prepaid card loaded with your discretionary budget. When it is empty, wait for next month.', 'budgeting', '💳', true),
        ('Bill Negotiation', 'Call service providers annually to negotiate better rates. Many offer loyalty discounts if you ask.', 'budgeting', '📞', true),
        ('Bulk Buying', 'Buy non-perishables in bulk when on sale. Calculate cost per unit to ensure actual savings.', 'budgeting', '📦', true),
        ('Utility Savings', 'Turn off lights, unplug devices, use energy-efficient bulbs. Small habits reduce electricity bills significantly.', 'budgeting', '💡', true),
        ('Transport Optimization', 'Compare costs: owning a car vs Uber/Bolt vs public transport. Choose what makes financial sense.', 'budgeting', '🚗', true),
        ('DIY When Possible', 'Learn basic repairs and maintenance. YouTube tutorials can save you thousands in service fees.', 'budgeting', '🔧', true),
        ('Shopping Lists', 'Always shop with a list and stick to it. Stores are designed to encourage impulse purchases.', 'budgeting', '📝', true),
        ('Budget Review', 'Adjust your budget when life changes: new job, new baby, relocation. Budgets should evolve with you.', 'budgeting', '🔄', true),

        -- Investing Tips (20)
        ('Start Early', 'Time in the market beats timing the market. Starting at 25 vs 35 can double your retirement fund due to compound interest.', 'investing', '📈', true),
        ('Compound Interest', 'Albert Einstein called it the 8th wonder of the world. ₦100,000 at 10% becomes ₦259,374 in 10 years, doing nothing!', 'investing', '🧮', true),
        ('Diversification', 'Never put all eggs in one basket. Spread investments across stocks, bonds, real estate, and savings.', 'investing', '🌐', true),
        ('Index Funds', 'Low-cost index funds often outperform actively managed funds. Less fees = more money in your pocket.', 'investing', '📊', true),
        ('Dollar-Cost Averaging', 'Invest fixed amounts regularly regardless of market conditions. This reduces the impact of volatility.', 'investing', '💵', true),
        ('Risk Tolerance', 'Young investors can take more risk (more stocks). As you age, shift toward safer investments (bonds).', 'investing', '⚖️', true),
        ('Treasury Bills', 'Nigerian treasury bills are low-risk investments backed by government. Good for emergency funds earning interest.', 'investing', '🏛️', true),
        ('Real Estate Basics', 'Real estate builds wealth but requires large capital. Consider REITs for fractional real estate investing.', 'investing', '🏠', true),
        ('Avoid Get-Rich-Quick', 'If it sounds too good to be true, it probably is. Ponzi schemes have cost Nigerians billions.', 'investing', '⚠️', true),
        ('Investment Education', 'Before investing in anything, understand it thoroughly. Never invest in what you do not understand.', 'investing', '📚', true),
        ('Long-Term Thinking', 'The stock market fluctuates daily but trends upward over decades. Stay invested during downturns.', 'investing', '🎢', true),
        ('Reinvest Dividends', 'When you receive dividends, reinvest them. This accelerates compound growth significantly.', 'investing', '🔄', true),
        ('Investment Fees', 'High fees eat returns. A 2% fee vs 0.5% fee can cost hundreds of thousands over an investing lifetime.', 'investing', '💸', true),
        ('Emergency Fund First', 'Build 3-6 months emergency savings before investing aggressively. You do not want to sell investments in a crisis.', 'investing', '🛡️', true),
        ('Tax-Advantaged Accounts', 'Use pension plans and other tax-advantaged accounts. Pay less tax = keep more money.', 'investing', '📋', true),
        ('Retirement Planning', 'Start retirement planning in your 20s. Even ₦20,000/month can grow to over ₦50 million by retirement.', 'investing', '👴', true),
        ('Investment Apps', 'Use licensed investment apps like Bamboo, Chaka, or Risevest to access global markets legally from Nigeria.', 'investing', '📱', true),
        ('Patience Pays', 'Warren Buffett made 99% of his wealth after age 50. Wealth building is a marathon, not a sprint.', 'investing', '🐢', true),
        ('Stay Informed', 'Follow financial news but do not react emotionally. Make decisions based on strategy, not headlines.', 'investing', '📰', true),
        ('Review Annually', 'Rebalance your investment portfolio yearly to maintain your target asset allocation.', 'investing', '📆', true),

        -- Debt Management Tips (20)
        ('Good vs Bad Debt', 'Good debt (education, business) can increase earning potential. Bad debt (consumer items) drains wealth.', 'debt_management', '⚖️', true),
        ('Debt Snowball', 'Pay minimum on all debts, throw extra at the smallest debt. When it is paid, roll that payment to the next.', 'debt_management', '❄️', true),
        ('Debt Avalanche', 'Pay minimum on all debts, throw extra at the highest interest debt first. Mathematically optimal.', 'debt_management', '🏔️', true),
        ('Know Your Interest', 'List all debts with their interest rates. Credit cards (30%+) should be paid before loans (15-25%).', 'debt_management', '📊', true),
        ('Avoid Minimum Payments', 'Paying only minimums stretches debt for years and multiplies what you pay. Always pay extra when possible.', 'debt_management', '⏰', true),
        ('Negotiate Interest', 'Call creditors and ask for lower interest rates. Many will reduce rates for customers with good payment history.', 'debt_management', '📞', true),
        ('Credit Card Traps', 'Only use credit cards if you can pay the full balance monthly. Interest charges quickly spiral out of control.', 'debt_management', '💳', true),
        ('Debt Consolidation', 'If you have multiple high-interest debts, consider a lower-interest consolidation loan. Do the math first!', 'debt_management', '🔗', true),
        ('Stop Bleeding', 'While paying off debt, avoid taking on new debt. Cut up extra credit cards if needed.', 'debt_management', '🛑', true),
        ('Emergency Fund While in Debt', 'Keep a small emergency fund (₦50,000) even while paying debt, to avoid new debt for emergencies.', 'debt_management', '🛡️', true),
        ('Side Income for Debt', 'Consider a side hustle dedicated to debt repayment. Extra income accelerates freedom.', 'debt_management', '💼', true),
        ('Track Debt Progress', 'Visualize debt payoff with a chart or app. Watching numbers decrease is motivating.', 'debt_management', '📉', true),
        ('Windfalls to Debt', 'Apply unexpected money (bonuses, gifts, tax refunds) to debt rather than spending it.', 'debt_management', '🎯', true),
        ('Debt-Free Date', 'Calculate your debt-free date at current payment rate. Work to bring that date closer.', 'debt_management', '📅', true),
        ('Lifestyle During Debt', 'Live below your means while paying off debt. Temporary sacrifice for permanent freedom.', 'debt_management', '🏠', true),
        ('Avoid Loan Sharks', 'Never borrow from unlicensed lenders. Their interest rates and practices are predatory and illegal.', 'debt_management', '⚠️', true),
        ('Understand Loan Terms', 'Read all loan terms carefully before signing. Know total cost, not just monthly payment.', 'debt_management', '📜', true),
        ('Co-signing Danger', 'Avoid co-signing loans. If the borrower defaults, you are legally responsible for the full amount.', 'debt_management', '✍️', true),
        ('Debt and Mental Health', 'Debt causes stress. Seek support from family or professionals. You are not alone, and solutions exist.', 'debt_management', '🧠', true),
        ('Celebrate Payoffs', 'When you pay off a debt, celebrate! Then immediately redirect that payment to the next debt.', 'debt_management', '🎉', true),

        -- General Financial Tips (20)
        ('Financial Goals', 'Write down specific financial goals with deadlines. Vague hopes rarely become reality.', 'general', '🎯', true),
        ('Money Mindset', 'Your beliefs about money shape your behavior. Challenge limiting beliefs like "rich people are greedy."', 'general', '🧠', true),
        ('Financial Literacy', 'Read one book about personal finance this year. Knowledge is the foundation of wealth.', 'general', '📚', true),
        ('Income Streams', 'The wealthy have multiple income streams. Consider side businesses, investments, or rental income.', 'general', '🌊', true),
        ('Protect Your Identity', 'Never share BVN, ATM pins, or OTPs. Banks will never call asking for these details.', 'general', '🔒', true),
        ('Insurance Basics', 'Insurance protects wealth. Consider health, life, and property insurance based on your situation.', 'general', '🛡️', true),
        ('Will and Estate', 'Create a will regardless of age or wealth. It protects your family and ensures your wishes are followed.', 'general', '📜', true),
        ('Financial Partner', 'Discuss money openly with your spouse/partner. Financial compatibility is crucial for relationship success.', 'general', '💑', true),
        ('Teach Children', 'Teach children about money early. Allowances, saving jars, and money conversations build future habits.', 'general', '👶', true),
        ('Avoid Comparisons', 'Do not compare your chapter 1 to someone else is chapter 20. Everyone is financial journey is different.', 'general', '🏃', true),
        ('Live Below Means', 'Spend less than you earn, always. This simple rule is the foundation of all wealth building.', 'general', '📉', true),
        ('Review Bank Statements', 'Check bank statements monthly for errors and unauthorized charges. Catch issues early.', 'general', '🔍', true),
        ('Build Credit History', 'Good credit history helps with loan approval and rates. Use credit responsibly to build it.', 'general', '📊', true),
        ('Financial Advisor', 'For complex situations, consult a licensed financial advisor. Good advice can save/earn millions.', 'general', '👔', true),
        ('Avoid Lifestyle Creep', 'As income increases, do not automatically increase spending. Direct raises to savings and investments.', 'general', '🚫', true),
        ('Network Value', 'Your network is your net worth. Build relationships with financially wise people.', 'general', '🤝', true),
        ('Time is Money', 'Consider the time cost of purchases. A ₦10,000 item might represent 5 hours of your work.', 'general', '⏰', true),
        ('Financial Independence', 'The goal is not just retirement, but financial independence: working because you want to, not because you have to.', 'general', '🏖️', true),
        ('Consistency Wins', 'Financial success is not about big wins but consistent small actions over time. Show up daily.', 'general', '📅', true),
        ('Start Today', 'The best time to start was 10 years ago. The second best time is today. Take action now!', 'general', '🚀', true);
    """)


def downgrade() -> None:
    # Remove seeded data
    op.execute("DELETE FROM financial_tips")
    op.execute("DELETE FROM badges")
    op.drop_table('financial_tips')
