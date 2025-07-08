import cloudinary
cloudinary.config(
    cloud_name='dnajh1ude',
    api_key='238245316481754',
    api_secret='492KLCWejjtO1LkHDCo7XEtWv_I'
)
import cloudinary.api
result = cloudinary.api.ping()
print(result)