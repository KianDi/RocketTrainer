import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  TrophyIcon,
  UserGroupIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  SparklesIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-rl-blue via-rl-purple to-rl-orange py-20 lg:py-32">
        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full text-white text-sm font-medium mb-6">
              <SparklesIcon className="w-4 h-4" />
              <span>AI-Powered Rocket League Coaching</span>
            </div>
            
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-gaming font-bold text-white mb-6">
              Master Rocket League
              <span className="block bg-gradient-to-r from-yellow-300 to-orange-300 bg-clip-text text-transparent">
                With AI Coaching
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-white/90 mb-8 max-w-3xl mx-auto">
              Upload your replays, get instant AI analysis, and receive personalized training 
              recommendations to rank up faster than ever before.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button asChild size="lg" className="bg-white text-rl-blue hover:bg-gray-100 text-lg px-8 py-6 h-auto">
                <Link to="/login">
                  Get Started Free
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="border-2 border-white text-white hover:bg-white/10 text-lg px-8 py-6 h-auto">
                <a href="#features">
                  Learn More
                </a>
              </Button>
            </div>
            
            <div className="mt-12 flex items-center justify-center gap-8 text-white/80 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-5 h-5" />
                <span>Free to start</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-5 h-5" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-5 h-5" />
                <span>Instant analysis</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 lg:py-32 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-gaming font-bold text-foreground mb-4">
              Why Choose RocketTrainer?
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Professional-level coaching powered by AI, available 24/7 at a fraction of the cost
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border-2 hover:border-rl-blue transition-colors">
              <CardHeader>
                <div className="w-12 h-12 bg-rl-blue rounded-lg flex items-center justify-center mb-4">
                  <ChartBarIcon className="w-6 h-6 text-white" />
                </div>
                <CardTitle className="text-xl">Smart Analysis</CardTitle>
                <CardDescription>
                  AI analyzes your replays to identify specific weaknesses in your gameplay across 8 skill categories
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-rl-purple transition-colors">
              <CardHeader>
                <div className="w-12 h-12 bg-rl-purple rounded-lg flex items-center justify-center mb-4">
                  <CpuChipIcon className="w-6 h-6 text-white" />
                </div>
                <CardTitle className="text-xl">Personalized Training</CardTitle>
                <CardDescription>
                  Get custom training pack recommendations based on your specific needs and skill level
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-rl-orange transition-colors">
              <CardHeader>
                <div className="w-12 h-12 bg-rl-orange rounded-lg flex items-center justify-center mb-4">
                  <TrophyIcon className="w-6 h-6 text-white" />
                </div>
                <CardTitle className="text-xl">Track Progress</CardTitle>
                <CardDescription>
                  Monitor your improvement over time with detailed analytics and performance insights
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-rl-green transition-colors">
              <CardHeader>
                <div className="w-12 h-12 bg-rl-green rounded-lg flex items-center justify-center mb-4">
                  <UserGroupIcon className="w-6 h-6 text-white" />
                </div>
                <CardTitle className="text-xl">Find Partners</CardTitle>
                <CardDescription>
                  Connect with players at your skill level for training sessions and improvement
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 lg:py-32 bg-muted/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-gaming font-bold text-foreground mb-4">
              How It Works
            </h2>
            <p className="text-xl text-muted-foreground">
              Get started in 3 simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-rl-blue to-rl-purple rounded-full flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">
                  1
                </div>
                <CardTitle className="text-center">Upload Replays</CardTitle>
                <CardDescription className="text-center">
                  Upload your Rocket League replay files or connect your Ballchasing account
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-rl-purple to-rl-orange rounded-full flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">
                  2
                </div>
                <CardTitle className="text-center">Get AI Analysis</CardTitle>
                <CardDescription className="text-center">
                  Our AI analyzes your gameplay and identifies your top weaknesses with 90% accuracy
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-rl-orange to-rl-green rounded-full flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">
                  3
                </div>
                <CardTitle className="text-center">Train & Improve</CardTitle>
                <CardDescription className="text-center">
                  Follow personalized training recommendations and watch your rank improve
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 lg:py-32 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-gaming font-bold text-foreground mb-4">
              Proven Results
            </h2>
            <p className="text-xl text-muted-foreground">
              Join thousands of players who have improved their rank with RocketTrainer
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="text-5xl font-gaming font-bold bg-gradient-to-r from-rl-blue to-rl-purple bg-clip-text text-transparent mb-2">
                  25%
                </div>
                <div className="text-lg text-muted-foreground">Average Rank Improvement</div>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="text-5xl font-gaming font-bold bg-gradient-to-r from-rl-purple to-rl-orange bg-clip-text text-transparent mb-2">
                  10K+
                </div>
                <div className="text-lg text-muted-foreground">Replays Analyzed</div>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="text-5xl font-gaming font-bold bg-gradient-to-r from-rl-orange to-rl-green bg-clip-text text-transparent mb-2">
                  95%
                </div>
                <div className="text-lg text-muted-foreground">User Satisfaction</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 lg:py-32 bg-gradient-to-br from-gray-900 to-gray-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <RocketLaunchIcon className="w-16 h-16 mx-auto mb-6 text-yellow-300" />
          <h2 className="text-3xl md:text-5xl font-gaming font-bold mb-6">
            Ready to Rank Up?
          </h2>
          <p className="text-xl mb-8 text-gray-300">
            Start your journey to Grand Champion today with personalized AI coaching
          </p>
          <Button asChild size="lg" className="bg-rl-blue hover:bg-blue-700 text-white text-lg px-8 py-6 h-auto">
            <Link to="/login">
              Start Training Now
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Link>
          </Button>
          <p className="mt-6 text-sm text-gray-400">
            No credit card required • Free to start • Cancel anytime
          </p>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;

