import React, { useState } from 'react'

interface Project {
  id: number
  name: string
  description: string
  status: 'Draft' | 'Active' | 'Published' | 'Archived'
  videos: number
  createdAt: string
  thumbnail: string
}

export const Projects: React.FC = () => {
  const [projects] = useState<Project[]>([
    {
      id: 1,
      name: 'Tech Review Series',
      description: 'In-depth reviews of the latest technology products',
      status: 'Active',
      videos: 8,
      createdAt: '2024-01-15',
      thumbnail: '🔧'
    },
    {
      id: 2,
      name: 'Cooking Tutorial',
      description: 'Easy recipes for beginners',
      status: 'Draft',
      videos: 3,
      createdAt: '2024-01-10',
      thumbnail: '👨‍🍳'
    },
    {
      id: 3,
      name: 'Travel Vlog',
      description: 'Adventures around the world',
      status: 'Published',
      videos: 12,
      createdAt: '2024-01-05',
      thumbnail: '✈️'
    },
    {
      id: 4,
      name: 'Fitness Journey',
      description: 'Daily workout routines and tips',
      status: 'Active',
      videos: 15,
      createdAt: '2024-01-01',
      thumbnail: '💪'
    }
  ])

  const [filter, setFilter] = useState<string>('All')
  const filters = ['All', 'Draft', 'Active', 'Published', 'Archived']

  const filteredProjects = filter === 'All' 
    ? projects 
    : projects.filter(project => project.status === filter)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800'
      case 'Draft': return 'bg-yellow-100 text-yellow-800'
      case 'Published': return 'bg-blue-100 text-blue-800'
      case 'Archived': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600">Manage your video content projects</p>
        </div>
        <button className="btn-primary">
          + New Project
        </button>
      </div>

      {/* Filters */}
      <div className="flex space-x-2">
        {filters.map((filterOption) => (
          <button
            key={filterOption}
            onClick={() => setFilter(filterOption)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === filterOption
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {filterOption}
          </button>
        ))}
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProjects.map((project) => (
          <div key={project.id} className="card hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center">
                <span className="text-3xl mr-3">{project.thumbnail}</span>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(project.status)}`}>
                    {project.status}
                  </span>
                </div>
              </div>
              <button className="text-gray-400 hover:text-gray-600">
                ⋮
              </button>
            </div>
            
            <p className="text-gray-600 text-sm mb-4 line-clamp-2">
              {project.description}
            </p>
            
            <div className="flex justify-between items-center text-sm text-gray-500">
              <span>{project.videos} videos</span>
              <span>Created {new Date(project.createdAt).toLocaleDateString()}</span>
            </div>
            
            <div className="mt-4 flex space-x-2">
              <button className="flex-1 btn-primary text-sm py-2">
                Open
              </button>
              <button className="flex-1 btn-secondary text-sm py-2">
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <span className="text-6xl mb-4 block">📁</span>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
          <p className="text-gray-500 mb-4">
            {filter === 'All' 
              ? "You haven't created any projects yet." 
              : `No projects with status "${filter}".`}
          </p>
          <button className="btn-primary">
            Create your first project
          </button>
        </div>
      )}
    </div>
  )
}