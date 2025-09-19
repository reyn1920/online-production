import React, { useState } from 'react'

export const Analytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState('7d')
  
  const metrics = [
    { name: 'Total Views', value: '2.4M', change: '+12.5%', trend: 'up' },
    { name: 'Watch Time', value: '18.2K hrs', change: '+8.3%', trend: 'up' },
    { name: 'Subscribers', value: '45.2K', change: '+15.7%', trend: 'up' },
    { name: 'Engagement Rate', value: '12.8%', change: '-2.1%', trend: 'down' },
  ]

  const topVideos = [
    { title: 'iPhone 15 Pro Review', views: '1.2M', duration: '12:34', engagement: '15.2%' },
    { title: 'Best Coding Setup 2024', views: '890K', duration: '8:45', engagement: '18.7%' },
    { title: 'Travel Photography Tips', views: '654K', duration: '15:22', engagement: '12.3%' },
    { title: 'Healthy Meal Prep Guide', views: '432K', duration: '10:18', engagement: '14.8%' },
  ]

  const audienceData = [
    { age: '18-24', percentage: 25, gender: { male: 60, female: 40 } },
    { age: '25-34', percentage: 35, gender: { male: 55, female: 45 } },
    { age: '35-44', percentage: 22, gender: { male: 50, female: 50 } },
    { age: '45-54', percentage: 12, gender: { male: 45, female: 55 } },
    { age: '55+', percentage: 6, gender: { male: 40, female: 60 } },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Track your content performance</p>
        </div>
        <div className="flex space-x-2">
          {['7d', '30d', '90d', '1y'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => (
          <div key={metric.name} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{metric.name}</p>
                <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              </div>
              <div className={`flex items-center text-sm font-medium ${
                metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
              }`}>
                <span className="mr-1">{metric.trend === 'up' ? '↗️' : '↘️'}</span>
                {metric.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Views Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Views Over Time</h3>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <span className="text-4xl mb-2 block">📈</span>
              <p className="text-gray-600">Chart visualization would go here</p>
              <p className="text-sm text-gray-500">Integration with charting library needed</p>
            </div>
          </div>
        </div>

        {/* Engagement Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement Metrics</h3>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <span className="text-4xl mb-2 block">💬</span>
              <p className="text-gray-600">Engagement chart would go here</p>
              <p className="text-sm text-gray-500">Shows likes, comments, shares</p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Performing Videos */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Performing Videos</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Video Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Views
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Engagement
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {topVideos.map((video, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {video.title}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {video.views}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {video.duration}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {video.engagement}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audience Demographics */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Audience Demographics</h3>
        <div className="space-y-4">
          {audienceData.map((demo) => (
            <div key={demo.age} className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm font-medium text-gray-900 w-12">{demo.age}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2 w-32">
                  <div 
                    className="bg-primary-600 h-2 rounded-full" 
                    style={{ width: `${demo.percentage}%` }}
                  ></div>
                </div>
                <span className="text-sm text-gray-600">{demo.percentage}%</span>
              </div>
              <div className="flex space-x-2 text-xs text-gray-500">
                <span>♂ {demo.gender.male}%</span>
                <span>♀ {demo.gender.female}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}