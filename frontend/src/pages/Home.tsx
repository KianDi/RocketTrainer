import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  TrophyIcon,
  UserGroupIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

const Home: React.FC = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="gaming-gradient text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-6xl font-gaming font-bold mb-6">
            Level Up Your
            <span className="block text-yellow-300">Rocket League</span>
            Game
          </h1>
          <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto">
            AI-powered analysis of your replays identifies weaknesses and creates 
            personalized training routines to boost your rank.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/login"
              className="bg-white text-rl-blue px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors inline-flex items-center justify-center"
            >
              Get Started Free
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Link>
            <button className="border-2 border-white text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-white hover:text-rl-blue transition-colors">
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-gaming font-bold text-gray-900 mb-4">
              Why RocketTrainer?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Professional-level coaching powered by AI, available 24/7 at a fraction of the cost.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-rl-blue rounded-lg flex items-center justify-center mx-auto mb-4">
                <ChartBarIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Smart Analysis</h3>
              <p className="text-gray-600">
                AI analyzes your replays to identify specific weaknesses in your gameplay.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-rl-purple rounded-lg flex items-center justify-center mx-auto mb-4">
                <CpuChipIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Personalized Training</h3>
              <p className="text-gray-600">
                Get custom training pack recommendations based on your specific needs.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-rl-orange rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrophyIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Track Progress</h3>
              <p className="text-gray-600">
                Monitor your improvement over time with detailed analytics and insights.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-rl-green rounded-lg flex items-center justify-center mx-auto mb-4">
                <UserGroupIcon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Find Partners</h3>
              <p className="text-gray-600">
                Connect with players at your skill level for training sessions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-gaming font-bold text-gray-900 mb-4">
              Proven Results
            </h2>
            <p className="text-xl text-gray-600">
              Join thousands of players who have improved their rank with RocketTrainer.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl font-gaming font-bold text-rl-blue mb-2">25%</div>
              <div className="text-lg text-gray-600">Average Rank Improvement</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-gaming font-bold text-rl-purple mb-2">10K+</div>
              <div className="text-lg text-gray-600">Replays Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-gaming font-bold text-rl-orange mb-2">95%</div>
              <div className="text-lg text-gray-600">User Satisfaction</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-gaming font-bold mb-6">
            Ready to Rank Up?
          </h2>
          <p className="text-xl mb-8">
            Start your journey to Grand Champion today with personalized AI coaching.
          </p>
          <Link
            to="/login"
            className="bg-rl-blue hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-bold text-lg transition-colors inline-flex items-center"
          >
            Start Training Now
            <ArrowRightIcon className="w-5 h-5 ml-2" />
          </Link>
        </div>
      </section>
    </div>
  );
};

export default Home;
