import React from 'react'
import { useAuth } from '../contexts/AuthContext'

export const Dashboard: React.FC = () => {
  const { user } = useAuth()

  const stats = [
    { name: 'Total Projects', value: '12', icon: '📁', change: '+2.1%' },
    { name: 'Videos Created', value: '48', icon: '🎬', change: '+15.3%' },
    { name: 'Total Views', value: '2.4M', icon: '👁️', change: '+8.2%' },
    { name: 'Engagement Rate', value: '12.5%', icon: '💬', change: '+3.1%' },
  ]

  const recentProjects = [
    { id: 1, name: 'Tech Review Series', status: 'Active', videos: 8, lastUpdated: '2 hours ago' },
    { id: 2, name: 'Cooking Tutorial', status: 'Draft', videos: 3, lastUpdated: '1 day ago' },
    { id: 3, name: 'Travel Vlog', status: 'Published', videos: 12, lastUpdated: '3 days ago' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-5">
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          Welcome back, {user?.username}!
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Here's what's happening with your content creation today.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">{stat.icon}</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </div>
                    <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Projects */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Recent Projects</h2>
          <button className="btn-primary">
            New Project
          </button>
        </div>
        <div className="overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Project
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Videos
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentProjects.map((project) => (
                <tr key={project.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {project.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      project.status === 'Active' ? 'bg-green-100 text-green-800' :
                      project.status === 'Draft' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {project.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {project.videos}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {project.lastUpdated}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center">
            <span className="text-3xl mr-4">🎬</span>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Create Video</h3>
              <p className="text-sm text-gray-500">Start a new video project</p>
            </div>
          </div>
        </div>
        <div className="card hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center">
            <span className="text-3xl mr-4">📊</span>
            <div>
              <h3 className="text-lg font-medium text-gray-900">View Analytics</h3>
              <p className="text-sm text-gray-500">Check your performance</p>
            </div>
          </div>
        </div>
        <div className="card hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center">
            <span className="text-3xl mr-4">🔍</span>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Research Topics</h3>
              <p className="text-sm text-gray-500">Find trending content</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}