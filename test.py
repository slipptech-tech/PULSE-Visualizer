image = pipe(prompt).images[0]
image.save("result.png,jpg,webp")

video = pipe(prompt).images[0]
video.save("result.mp4")

audio = pipe(prompt).images[0]
audio.save("result.wav")
